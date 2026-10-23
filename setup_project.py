import os

# Define the complete folder structure
DIRECTORIES = [
    "police_profile_360/app/models",
    "police_profile_360/app/routes",
    "police_profile_360/app/services",
    "police_profile_360/app/utils",
    "police_profile_360/app/static/css",
    "police_profile_360/app/static/js",
    "police_profile_360/app/static/img",
    "police_profile_360/app/templates/auth",
    "police_profile_360/app/templates/dashboard",
    "police_profile_360/app/templates/profiles",
    "police_profile_360/app/templates/search",
    "police_profile_360/app/templates/admin",
    "police_profile_360/tests",
]

# Define starter files and initial content
FILES = {
    # Dependencies
    "police_profile_360/requirements.txt": (
        "Flask==3.0.3\n"
        "pymongo==4.7.2\n"
        "Flask-Bcrypt==1.0.1\n"
        "python-dotenv==1.0.1\n"
        "gunicorn==22.0.0\n"
    ),
    # Deployment Procfile
    "police_profile_360/Procfile": "web: gunicorn run:app --bind 0.0.0.0:$PORT\n",
    # Environment configs
    "police_profile_360/.env.example": (
        "SECRET_KEY=generate_a_strong_random_secret_here\n"
        "MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/police_db?retryWrites=true&w=majority\n"
        "PORT=5000\n"
    ),
    "police_profile_360/.gitignore": (
        "venv/\n"
        "*.pyc\n"
        "__pycache__/\n"
        ".env\n"
        ".DS_Store\n"
    ),
    # App entry point
    "police_profile_360/run.py": (
        "import os\n"
        "from app import create_app\n\n"
        "app = create_app()\n\n"
        "if __name__ == '__main__':\n"
        "    port = int(os.environ.get('PORT', 5000))\n"
        "    app.run(host='0.0.0.0', port=port, debug=True)\n"
    ),
    # Flask factory
    "police_profile_360/app/__init__.py": (
        "import os\n"
        "from flask import Flask\n"
        "from pymongo import MongoClient\n"
        "from dotenv import load_dotenv\n\n"
        "load_dotenv()\n\n"
        "mongo_client = None\n"
        "db = None\n\n"
        "def create_app():\n"
        "    app = Flask(__name__)\n"
        "    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key')\n\n"
        "    global mongo_client, db\n"
        "    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/police_db')\n"
        "    mongo_client = MongoClient(mongo_uri)\n"
        "    db = mongo_client.get_default_database()\n\n"
        "    # Register Blueprints\n"
        "    from app.routes.auth import auth_bp\n"
        "    from app.routes.dashboard import dashboard_bp\n"
        "    from app.routes.profiles import profiles_bp\n"
        "    from app.routes.search import search_bp\n"
        "    from app.routes.admin import admin_bp\n\n"
        "    app.register_blueprint(auth_bp)\n"
        "    app.register_blueprint(dashboard_bp)\n"
        "    app.register_blueprint(profiles_bp, url_prefix='/profiles')\n"
        "    app.register_blueprint(search_bp, url_prefix='/search')\n"
        "    app.register_blueprint(admin_bp, url_prefix='/admin')\n\n"
        "    return app\n"
    ),
    # Python package markers
    "police_profile_360/app/models/__init__.py": "",
    "police_profile_360/app/routes/__init__.py": "",
    "police_profile_360/app/services/__init__.py": "",
    "police_profile_360/app/utils/__init__.py": "",
    "police_profile_360/tests/__init__.py": "",
    # Auth Blueprint
    "police_profile_360/app/routes/auth.py": (
        "from flask import Blueprint, render_template, request, redirect, url_for, session\n\n"
        "auth_bp = Blueprint('auth', __name__)\n\n"
        "@auth_bp.route('/', methods=['GET', 'POST'])\n"
        "@auth_bp.route('/login', methods=['GET', 'POST'])\n"
        "def login():\n"
        "    if request.method == 'POST':\n"
        "        # Handle login verification logic\n"
        "        session['user'] = request.form.get('username')\n"
        "        session['role'] = 'Admin'  # Default for testing\n"
        "        return redirect(url_for('dashboard.index'))\n"
        "    return render_template('auth/login.html')\n\n"
        "@auth_bp.route('/logout')\n"
        "def logout():\n"
        "    session.clear()\n"
        "    return redirect(url_for('auth.login'))\n"
    ),
    # Dashboard Blueprint
    "police_profile_360/app/routes/dashboard.py": (
        "from flask import Blueprint, render_template, session, redirect, url_for\n\n"
        "dashboard_bp = Blueprint('dashboard', __name__)\n\n"
        "@dashboard_bp.route('/dashboard')\n"
        "def index():\n"
        "    if 'user' not in session:\n"
        "        return redirect(url_for('auth.login'))\n"
        "    return render_template('dashboard/index.html', user=session['user'])\n"
    ),
    # Profiles Blueprint
    "police_profile_360/app/routes/profiles.py": (
        "from flask import Blueprint, render_template, session, redirect, url_for\n\n"
        "profiles_bp = Blueprint('profiles', __name__)\n\n"
        "@profiles_bp.route('/create', methods=['GET', 'POST'])\n"
        "def create():\n"
        "    if 'user' not in session:\n"
        "        return redirect(url_for('auth.login'))\n"
        "    return render_template('profiles/create.html')\n"
    ),
    # Search Blueprint
    "police_profile_360/app/routes/search.py": (
        "from flask import Blueprint, render_template, session, redirect, url_for\n\n"
        "search_bp = Blueprint('search', __name__)\n\n"
        "@search_bp.route('/', methods=['GET'])\n"
        "def query():\n"
        "    if 'user' not in session:\n"
        "        return redirect(url_for('auth.login'))\n"
        "    return render_template('search/search.html')\n"
    ),
    # Admin Blueprint
    "police_profile_360/app/routes/admin.py": (
        "from flask import Blueprint, render_template, session, redirect, url_for\n\n"
        "admin_bp = Blueprint('admin', __name__)\n\n"
        "@admin_bp.route('/users')\n"
        "def users():\n"
        "    if session.get('role') != 'Admin':\n"
        "        return 'Unauthorized', 403\n"
        "    return render_template('admin/users.html')\n"
    ),
    # Base layout
    "police_profile_360/app/templates/base.html": (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "    <meta charset='UTF-8'>\n"
        "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        "    <title>{% block title %}Police Profile 360{% endblock %}</title>\n"
        "    <script src='https://cdn.tailwindcss.com'></script>\n"
        "</head>\n"
        "<body class='bg-slate-100 text-slate-900'>\n"
        "    {% block content %}{% endblock %}\n"
        "</body>\n"
        "</html>\n"
    ),
    # Gatekeeper Login View
    "police_profile_360/app/templates/auth/login.html": (
        "{% extends 'base.html' %}\n"
        "{% block title %}Gatekeeper Login - Police Profile 360{% endblock %}\n"
        "{% block content %}\n"
        "<div class='min-h-screen flex items-center justify-center p-4'>\n"
        "    <div class='bg-white shadow-xl rounded-lg max-w-md w-full p-8 border border-slate-200'>\n"
        "        <div class='text-center mb-6'>\n"
        "            <h1 class='text-2xl font-bold tracking-tight text-slate-800'>POLICE PROFILE 360</h1>\n"
        "            <p class='text-sm text-red-600 font-semibold mt-1'>अति-गोपनीय अंतर्गत वापर</p>\n"
        "        </div>\n"
        "        <form method='POST' action='/login' class='space-y-4'>\n"
        "            <div>\n"
        "                <label class='block text-xs font-semibold uppercase text-slate-600 mb-1'>Officer ID / Username</label>\n"
        "                <input type='text' name='username' required class='w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600'>\n"
        "            </div>\n"
        "            <div>\n"
        "                <label class='block text-xs font-semibold uppercase text-slate-600 mb-1'>Passcode / Password</label>\n"
        "                <input type='password' name='password' required class='w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600'>\n"
        "            </div>\n"
        "            <button type='submit' class='w-full bg-blue-700 hover:bg-blue-800 text-white font-medium py-2 rounded text-sm transition-colors'>Secure Gatekeeper Login</button>\n"
        "        </form>\n"
        "    </div>\n"
        "</div>\n"
        "{% endblock %}\n"
    ),
    # Minimal Dashboard View
    "police_profile_360/app/templates/dashboard/index.html": (
        "{% extends 'base.html' %}\n"
        "{% block title %}Dashboard - Police Profile 360{% endblock %}\n"
        "{% block content %}\n"
        "<header class='bg-slate-900 text-white px-6 py-4 flex justify-between items-center'>\n"
        "    <div class='font-bold tracking-wide'>POLICE PROFILE 360</div>\n"
        "    <div class='flex items-center gap-4 text-sm'>\n"
        "        <span>Officer: <strong>{{ user }}</strong></span>\n"
        "        <a href='/logout' class='bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-xs'>Logout</a>\n"
        "    </div>\n"
        "</header>\n"
        "<main class='max-w-7xl mx-auto p-6'>\n"
        "    <h2 class='text-xl font-bold mb-4'>System Dashboard</h2>\n"
        "    <div class='grid grid-cols-1 md:grid-cols-3 gap-6'>\n"
        "        <div class='bg-white p-6 rounded shadow border border-slate-200'>\n"
        "            <div class='text-xs font-semibold text-slate-500 uppercase'>Total Profiles</div>\n"
        "            <div class='text-3xl font-extrabold mt-2'>0</div>\n"
        "        </div>\n"
        "        <div class='bg-white p-6 rounded shadow border border-slate-200'>\n"
        "            <div class='text-xs font-semibold text-slate-500 uppercase'>Active Cases</div>\n"
        "            <div class='text-3xl font-extrabold mt-2'>0</div>\n"
        "        </div>\n"
        "        <div class='bg-white p-6 rounded shadow border border-slate-200'>\n"
        "            <div class='text-xs font-semibold text-slate-500 uppercase'>Audit Events</div>\n"
        "            <div class='text-3xl font-extrabold mt-2'>0</div>\n"
        "        </div>\n"
        "    </div>\n"
        "</main>\n"
        "{% endblock %}\n"
    ),
    "police_profile_360/app/templates/profiles/create.html": "{% extends 'base.html' %}\n{% block content %}<div class='p-8'>New Profile Form (Under Construction)</div>{% endblock %}",
    "police_profile_360/app/templates/search/search.html": "{% extends 'base.html' %}\n{% block content %}<div class='p-8'>Smart Search View (Under Construction)</div>{% endblock %}",
    "police_profile_360/app/templates/admin/users.html": "{% extends 'base.html' %}\n{% block content %}<div class='p-8'>Admin User Controls (Under Construction)</div>{% endblock %}",
}


def build_scaffold():
    print("Creating directories...")
    for directory in DIRECTORIES:
        os.makedirs(directory, exist_ok=True)
        print(f"  [+] {directory}")

    print("\nWriting starter files...")
    for filepath, content in FILES.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] {filepath}")

    print("\nScaffolding complete: `police_profile_360/` is ready.")


if __name__ == "__main__":
    build_scaffold()