from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import db
from app.models.user import User
from app.models.audit import AuditLog

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not name or not username or not password:
            flash("कृपया नाव, युझरनेम आणि पासवर्ड सर्व माहिती भरा.", "danger")
            return render_template('auth/login.html')

        if db is None:
            flash("डेटाबेस कनेक्शन त्रुटी. कृपया नंतर प्रयत्न करा.", "danger")
            return render_template('auth/login.html')

        user = db.users.find_one({"username": username})

        if user and User.verify_password(user.get('password_hash'), password):
            # Check name or fallback to full_name
            db_name = (user.get('name') or user.get('full_name') or '').strip()

            # If name is missing from older records, auto-fill it
            if not db_name:
                db.users.update_one({"_id": user["_id"]}, {"$set": {"name": name, "full_name": name}})
                db_name = name

            # Case-insensitive comparison
            if db_name.lower() != name.lower():
                flash(f"नाव जुळत नाही. सिस्टिममध्ये नोंदवलेले नाव: '{db_name}'", "danger")
                return render_template('auth/login.html')

            # Populate session
            session['user'] = user.get('username')
            session['officer_name'] = db_name
            session['role'] = user.get('role', 'Read-Only')
            session['station'] = user.get('station', '-')

            AuditLog.create_entry(
                db,
                officer_id=user.get('username'),
                action="LOGIN_SUCCESS",
                details=f"Officer {db_name} logged in."
            )
            return redirect(url_for('dashboard.index'))
        else:
            flash("अवैध युझरनेम किंवा पासवर्ड.", "danger")

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    officer = session.get('user', 'Unknown')
    if db is not None:
        try:
            AuditLog.create_entry(
                db,
                officer_id=officer,
                action="LOGOUT",
                details=f"Officer {session.get('officer_name', officer)} logged out."
            )
        except Exception:
            pass

    session.clear()
    flash("आपण सुरक्षितपणे लॉगआउट झाला आहात.", "info")
    return redirect(url_for('auth.login'))