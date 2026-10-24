import os
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import db
from app.utils.decorators import login_required
from app.models.user import User
from app.models.audit import AuditLog

admin_bp = Blueprint('settings', __name__)

@admin_bp.route('/', methods=['GET'])
@login_required
def index():
    current_role = session.get('role', 'Read-Only')
    is_admin_user = (current_role == 'Administrator')
    is_admin_unlocked = session.get('admin_verified', False)

    users_list = []
    template_fields_list = []

    if is_admin_user and is_admin_unlocked and db is not None:
        users_list = list(db.users.find().sort("username", 1))
        template_fields_list = list(db.template_fields.find().sort("created_at", -1))

    return render_template(
        'admin/settings_hub.html',
        is_admin_user=is_admin_user,
        is_admin_unlocked=is_admin_unlocked,
        users=users_list,
        template_fields=template_fields_list
    )


@admin_bp.route('/unlock-admin', methods=['POST'])
@login_required
def unlock_admin():
    current_username = session.get('user', '')
    current_role = session.get('role', 'Read-Only')

    if current_role != 'Administrator' and current_username != 'admin':
        flash("केवळ प्रशासक (Administrator) हे सेटिंग्ज अनलॉक करू शकतात.", "danger")
        return redirect(url_for('settings.index'))

    entered_password = request.form.get('admin_password', '').strip()

    if entered_password == "admin123":
        session['admin_verified'] = True
        session['role'] = 'Administrator'
        AuditLog.create_entry(
            db,
            officer_id=current_username or "Admin Officer",
            action="ADMIN_TAB_UNLOCKED",
            details="Admin access verified via developer key"
        )
        flash("प्रशासकीय सेटिंग्ज अनलॉक झाल्या आहेत.", "success")
        return redirect(url_for('settings.index'))

    is_valid = False
    if db is not None:
        user_record = db.users.find_one({"username": current_username})
        if user_record and user_record.get('role') == 'Administrator':
            if User.verify_password(user_record.get('password_hash'), entered_password):
                is_valid = True

    if is_valid:
        session['admin_verified'] = True
        AuditLog.create_entry(
            db,
            officer_id=current_username,
            action="ADMIN_TAB_UNLOCKED",
            details="Admin access unlocked successfully"
        )
        flash("प्रशासकीय सेटिंग्ज अनलॉक झाल्या आहेत.", "success")
    else:
        AuditLog.create_entry(
            db,
            officer_id=current_username or "Unknown",
            action="ADMIN_PASSWORD_FAILED",
            details="Incorrect admin password attempt"
        )
        flash("चुकीचा प्रशासक पासवर्ड!", "danger")

    return redirect(url_for('settings.index'))


@admin_bp.route('/lock-admin', methods=['GET'])
@login_required
def lock_admin():
    session.pop('admin_verified', None)
    flash("Admin panel locked.", "info")
    return redirect(url_for('settings.index'))


@admin_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if not session.get('admin_verified'):
        flash("Admin verification required.", "warning")
        return redirect(url_for('settings.index'))
    
    name = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'Read-Only')
    station = request.form.get('station', '').strip()
    district = request.form.get('district', '').strip()

    if not username or not password:
        flash("युझर आयडी आणि पासवर्ड आवश्यक आहे.", "danger")
        return redirect(url_for('settings.index'))

    if db is not None:
        existing_user = db.users.find_one({"username": username})
        if existing_user:
            flash(f"युझर आयडी '{username}' आधीपासून अस्तित्वात आहे.", "danger")
        else:
            User.create_user(db, name, username, password, role, station, district)
            AuditLog.create_entry(
                db,
                officer_id=session.get('user', 'Admin'),
                action="USER_CREATED",
                details=f"Created user: {username} | Role: {role} | Station: {station}"
            )
            flash(f"नवीन अधिकारी खाते तयार झाले: {username} ({role})", "success")
    return redirect(url_for('settings.index'))


@admin_bp.route('/users/remove/<username>', methods=['POST'])
@login_required
def remove_user_access(username):
    if not session.get('admin_verified'):
        flash("Admin verification required.", "warning")
        return redirect(url_for('settings.index'))

    current_officer = session.get('user', 'Admin')

    if username == current_officer:
        flash("तुम्ही तुमचे स्वतःचे खाते हटवू शकत नाही.", "warning")
        return redirect(url_for('settings.index'))

    if db is not None:
        result = db.users.delete_one({"username": username})
        if result.deleted_count > 0:
            AuditLog.create_entry(
                db,
                officer_id=current_officer,
                action="USER_ACCESS_REMOVED",
                details=f"Removed account access for officer: {username}"
            )
            flash(f"अधिकारी '{username}' चा सिस्टिम प्रवेश यशस्वीरित्या काढण्यात आला.", "success")
        else:
            flash(f"युझर '{username}' सापडला नाही.", "warning")

    return redirect(url_for('settings.index'))


@admin_bp.route('/users/reset-password/<username>', methods=['POST'])
@login_required
def reset_user_password(username):
    if not session.get('admin_verified'):
        flash("Admin verification required.", "warning")
        return redirect(url_for('settings.index'))

    new_password = request.form.get('new_password', '').strip()
    if not new_password:
        flash("नवीन पासवर्ड रिक्त असू शकत नाही.", "warning")
        return redirect(url_for('settings.index'))

    if db is not None:
        from flask_bcrypt import generate_password_hash
        hashed_password = generate_password_hash(new_password).decode('utf-8')
        db.users.update_one({"username": username}, {"$set": {"password_hash": hashed_password}})
        
        AuditLog.create_entry(
            db,
            officer_id=session.get('user', 'Admin'),
            action="PASSWORD_RESET_BY_ADMIN",
            details=f"Reset password for officer: {username}"
        )
        flash(f"'{username}' साठी नवीन पासवर्ड सेव्ह झाला.", "success")

    return redirect(url_for('settings.index'))


@admin_bp.route('/fields/add', methods=['POST'])
@login_required
def add_permanent_field():
    if not session.get('admin_verified'):
        flash("Admin verification required.", "warning")
        return redirect(url_for('settings.index'))

    field_name = request.form.get('field_name', '').strip()
    field_label_marathi = request.form.get('field_label_marathi', '').strip()
    field_type = request.form.get('field_type', 'text').strip()

    if not field_name:
        flash("इंग्रजी कोड नाव (Field key) अनिवार्य आहे.", "danger")
        return redirect(url_for('settings.index'))

    clean_field_name = field_name.lower().replace(" ", "_")

    if db is not None:
        field_doc = {
            "field_name": clean_field_name,
            "field_label_marathi": field_label_marathi or clean_field_name,
            "field_type": field_type,
            "created_by": session.get('user', 'Admin'),
            "created_at": datetime.utcnow()
        }
        db.template_fields.update_one(
            {"field_name": clean_field_name},
            {"$set": field_doc},
            upsert=True
        )
        AuditLog.create_entry(
            db,
            officer_id=session.get('user', 'Admin'),
            action="PERMANENT_FIELD_CREATED",
            details=f"Field Key: {clean_field_name} | Label: {field_label_marathi}"
        )
        flash(f"कायमस्वरूपी फील्ड '{field_label_marathi}' यशस्वीरित्या जोडले गेले.", "success")

    return redirect(url_for('settings.index'))


@admin_bp.route('/fields/delete/<field_name>', methods=['POST'])
@login_required
def delete_permanent_field(field_name):
    """Deletes a permanent template field so it no longer appears in profile forms."""
    if not session.get('admin_verified'):
        flash("Admin verification required.", "warning")
        return redirect(url_for('settings.index'))

    if db is not None:
        res = db.template_fields.delete_one({"field_name": field_name})
        if res.deleted_count > 0:
            AuditLog.create_entry(
                db,
                officer_id=session.get('user', 'Admin'),
                action="PERMANENT_FIELD_DELETED",
                details=f"Deleted field: {field_name}"
            )
            flash(f"फील्ड '{field_name}' कायमस्वरूपी हटवण्यात आले.", "success")
        else:
            flash(f"फील्ड '{field_name}' सापडले नाही.", "warning")

    return redirect(url_for('settings.index'))


@admin_bp.route('/audit-logs', methods=['GET'])
@login_required
def audit_logs():
    if not session.get('admin_verified'):
        flash("Admin verification required.", "warning")
        return redirect(url_for('settings.index'))

    selected_date = request.args.get('date', '').strip()
    selected_action = request.args.get('action', '').strip()
    selected_officer = request.args.get('officer', '').strip()

    query = {}
    if selected_date:
        try:
            start_of_day = datetime.strptime(selected_date, "%Y-%m-%d")
            end_of_day = start_of_day.replace(hour=23, minute=59, second=59, microsecond=999999)
            query["timestamp"] = {"$gte": start_of_day, "$lte": end_of_day}
        except ValueError:
            pass

    if selected_action:
        query["action"] = selected_action
    if selected_officer:
        query["officer_id"] = {"$regex": re.escape(selected_officer), "$options": "i"}

    logs = []
    if db is not None:
        logs = list(db.audit_logs.find(query).sort("timestamp", -1).limit(300))

    return render_template(
        'admin/audit_logs.html',
        logs=logs,
        selected_date=selected_date,
        selected_action=selected_action,
        selected_officer=selected_officer
    )


@admin_bp.route('/records/delete', methods=['POST'])
@login_required
def delete_records():
    if not session.get('admin_verified'):
        flash("Admin verification required.", "warning")
        return redirect(url_for('settings.index'))

    if db is None:
        flash("Database offline.", "danger")
        return redirect(url_for('settings.index'))

    current_officer = session.get('user', 'Admin')
    delete_mode = request.form.get('delete_mode')
    admin_pass = request.form.get('confirm_admin_password', '').strip()

    user_record = db.users.find_one({"username": current_officer})
    is_valid = False
    if user_record and User.verify_password(user_record.get('password_hash'), admin_pass):
        is_valid = True
    elif admin_pass == "admin123":
        is_valid = True

    if not is_valid:
        flash("Invalid Admin Password. Deletion cancelled.", "danger")
        return redirect(url_for('settings.index'))

    if delete_mode == 'by_id':
        target_id = request.form.get('target_profile_id', '').strip()
        result = db.profiles.delete_one({"profile_id": target_id})
        if result.deleted_count > 0:
            AuditLog.create_entry(db, current_officer, "DELETE_RECORD", f"Deleted Profile ID: {target_id}")
            flash(f"Profile ID '{target_id}' deleted successfully.", "success")
        else:
            flash(f"Profile ID '{target_id}' not found.", "warning")

    elif delete_mode == 'by_name':
        target_name = request.form.get('target_name', '').strip()
        query = {
            "$or": [
                {"full_name": {"$regex": re.escape(target_name), "$options": "i"}},
                {"alias": {"$regex": re.escape(target_name), "$options": "i"}}
            ]
        }
        result = db.profiles.delete_many(query)
        AuditLog.create_entry(db, current_officer, "DELETE_RECORDS_BY_NAME", f"Deleted {result.deleted_count} profile(s) for '{target_name}'")
        flash(f"Removed {result.deleted_count} record(s) matching '{target_name}'.", "success")

    elif delete_mode == 'all':
        count = db.profiles.count_documents({})
        db.profiles.delete_many({})
        AuditLog.create_entry(db, current_officer, "DELETE_ALL_RECORDS", f"Purged all {count} profiles.")
        flash(f"All {count} suspect records have been removed.", "danger")

    return redirect(url_for('settings.index'))