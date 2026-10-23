from datetime import datetime
from flask import request

class AuditLog:
    @staticmethod
    def create_entry(db, officer_id: str, action: str, details: str = ""):
        """
        Records an immutable audit trace to MongoDB Atlas.
        """
        if db is None:
            return  # Prevents crashing if running offline without DB
            
        log_doc = {
            "officer_id": officer_id,
            "action": action,          # e.g., 'LOGIN', 'CREATE_PROFILE', 'VIEW_PROFILE'
            "details": details,
            "ip_address": request.remote_addr or "Unknown",
            "user_agent": request.headers.get('User-Agent', 'Unknown'),
            "timestamp": datetime.utcnow()
        }
        db.audit_logs.insert_one(log_doc)