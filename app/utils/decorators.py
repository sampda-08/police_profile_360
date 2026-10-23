from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """
    Decorator to ensure the officer is authenticated via the Gatekeeper login.
    If the session does not contain 'user', they are booted to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("कृपया पुढे जाण्यापूर्वी लॉगिन करा (Please login to continue).", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """
    Decorator to restrict sensitive endpoints (like Admin configurations)
    only to designated officer ranks.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('auth.login'))
            user_role = session.get('role', 'Read-Only')
            if user_role not in allowed_roles:
                flash("हा विभाग पाहण्याची तुम्हाला परवानगी नाही (Access Denied).", "danger")
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator