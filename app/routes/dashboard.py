from flask import Blueprint, render_template, session
from app import db
from app.utils.decorators import login_required

dashboard_bp = Blueprint('dashboard', __name__)

# Since url_prefix='/dashboard' is set in __init__.py,
# route('/') maps directly to /dashboard and /dashboard/
@dashboard_bp.route('/', methods=['GET'])
@dashboard_bp.route('/home', methods=['GET'])
@login_required
def index():
    profile_count = 0
    recent_logs = []
    
    if db is not None:
        profile_count = db.profiles.count_documents({})
        recent_logs = list(db.audit_logs.find().sort("timestamp", -1).limit(5))

    return render_template(
        'dashboard/index.html',
        user=session.get('user'),
        role=session.get('role'),
        station=session.get('station'),
        profile_count=profile_count,
        recent_logs=recent_logs
    )