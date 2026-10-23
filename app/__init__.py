import os
import certifi
from flask import Flask, session, request, redirect, url_for
from pymongo import MongoClient
from app.utils.translations import TRANSLATIONS

db = None

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'shorya-360-secret-key-2026')

    # Read Atlas URI from environment or fallback
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/police_profile_360')
    
    try:
        if "mongodb+srv://" in mongo_uri:
            client = MongoClient(
                mongo_uri,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000
            )
        else:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        global db
        db = client['police_profile_360']
        client.server_info()
        print("Connected to MongoDB -> Database: police_profile_360 | Count:", db.profiles.count_documents({}))

        # Establish Partial Unique Indexes using supported comparison operators ($gte, $lte)
        try:
            db.profiles.create_index(
                [("identity_docs.aadhaar_card_no", 1)],
                unique=True,
                partialFilterExpression={
                    "$and": [
                        {"identity_docs.aadhaar_card_no": {"$type": "string"}},
                        {"identity_docs.aadhaar_card_no": {"$gte": "000000000000"}},
                        {"identity_docs.aadhaar_card_no": {"$lte": "999999999999"}}
                    ]
                }
            )

            db.profiles.create_index(
                [("identity_docs.pan_card_no", 1)],
                unique=True,
                partialFilterExpression={
                    "$and": [
                        {"identity_docs.pan_card_no": {"$type": "string"}},
                        {"identity_docs.pan_card_no": {"$gte": "A"}},
                        {"identity_docs.pan_card_no": {"$lte": "ZZZZZZZZZZ"}}
                    ]
                }
            )
        except Exception as idx_err:
            print("Notice: Index setup skipped or already active:", idx_err)

    except Exception as e:
        print(f"MongoDB Connection Error: {e}")
        db = None

    # Global Language Context Processor
    @app.context_processor
    def inject_language_context():
        current_lang = session.get('lang', 'mr')
        def t(key, default=None):
            lang_dict = TRANSLATIONS.get(current_lang, TRANSLATIONS['mr'])
            return lang_dict.get(key, default or key)
        return dict(current_lang=current_lang, t=t)

    # Universal Language Switcher
    @app.route('/set-language/<lang>')
    def set_language(lang):
        if lang in ['mr', 'en', 'hi']:
            session['lang'] = lang
        return redirect(request.referrer or url_for('dashboard.index'))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.profiles import profiles_bp
    from app.routes.search import search_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(profiles_bp, url_prefix='/profiles')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(admin_bp, url_prefix='/settings')

    # Root Route
    @app.route('/')
    def root():
        if 'user' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # Lightweight Keep-Alive Endpoint for cron-job.org
    @app.route('/health')
    def health_ping():
        return {"status": "ok", "app": "SHORYA 360"}, 200

    return app