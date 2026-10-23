from flask_bcrypt import Bcrypt
from werkzeug.security import check_password_hash as werkzeug_check

bcrypt = Bcrypt()

class User:
    @staticmethod
    def create_user(db, name, username, plain_password, role, station, district):
        """
        Hashes password with bcrypt and stores officer details with full name in MongoDB.
        """
        password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')
        user_doc = {
            "name": name.strip(),
            "username": username.strip(),
            "password_hash": password_hash,
            "role": role,  # 'Administrator', 'Investigator', 'Reviewer', 'Read-Only'
            "station": station.strip(),
            "district": district.strip(),
            "failed_attempts": 0,
            "is_locked": False
        }
        return db.users.insert_one(user_doc)

    @staticmethod
    def verify_password(stored_hash, candidate_password):
        if not stored_hash or not candidate_password:
            return False
        try:
            return bcrypt.check_password_hash(stored_hash, candidate_password)
        except (ValueError, Exception):
            try:
                return werkzeug_check(stored_hash, candidate_password)
            except Exception:
                return False