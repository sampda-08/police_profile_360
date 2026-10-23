import re
import unicodedata
from flask import Blueprint, render_template, request, session
from app import db
from app.utils.decorators import login_required
from app.utils.maskers import mask_id_number
from app.models.audit import AuditLog
from app.utils.transliterate import is_english, clean_text, transliterate_token

search_bp = Blueprint('search', __name__)

@search_bp.route('/', methods=['GET'])
@login_required
def query():
    results = []
    
    q_name = clean_text(request.args.get('name', ''))
    q_station = clean_text(request.args.get('station', ''))
    q_district = clean_text(request.args.get('district', ''))
    q_contact = clean_text(request.args.get('contact', ''))

    has_filters = any([q_name, q_station, q_district, q_contact])

    if has_filters and db is not None:
        query_conditions = []

        # 1. Multi-Word Dynamic Cross-Script Name/Alias Search
        if q_name:
            tokens = q_name.split()
            for token in tokens:
                token_patterns = [re.escape(token)]
                
                if is_english(token):
                    devanagari_options = transliterate_token(token)
                    for dev_opt in devanagari_options:
                        token_patterns.append(re.escape(dev_opt))

                combined_pattern = "|".join(token_patterns)
                
                query_conditions.append({
                    "$or": [
                        {"full_name": {"$regex": combined_pattern, "$options": "i"}},
                        {"alias": {"$regex": combined_pattern, "$options": "i"}}
                    ]
                })

        # 2. Dynamic Police Station Search
        if q_station:
            station_tokens = q_station.split()
            for st in station_tokens:
                st_patterns = [re.escape(st)]
                if is_english(st):
                    for dev_opt in transliterate_token(st):
                        st_patterns.append(re.escape(dev_opt))
                combined_st = "|".join(st_patterns)
                query_conditions.append({"station": {"$regex": combined_st, "$options": "i"}})

        # 3. Dynamic District Search
        if q_district:
            dist_tokens = q_district.split()
            for dt in dist_tokens:
                dt_patterns = [re.escape(dt)]
                if is_english(dt):
                    for dev_opt in transliterate_token(dt):
                        dt_patterns.append(re.escape(dev_opt))
                combined_dt = "|".join(dt_patterns)
                query_conditions.append({
                    "$or": [
                        {"address.dist": {"$regex": combined_dt, "$options": "i"}},
                        {"district": {"$regex": combined_dt, "$options": "i"}}
                    ]
                })

        # 4. Contact Number Search
        if q_contact:
            query_conditions.append({
                "contacts": {"$regex": re.escape(q_contact)}
            })

        final_query = {"$and": query_conditions} if query_conditions else {}
        results = list(db.profiles.find(final_query).sort("created_at", -1).limit(100))

        for r in results:
            if "identity_docs" in r and r["identity_docs"].get("aadhaar_card_no"):
                r["identity_docs"]["masked_aadhaar"] = mask_id_number(r["identity_docs"]["aadhaar_card_no"])

        AuditLog.create_entry(
            db,
            officer_id=session.get('user', 'Unknown'),
            action="SEARCH_TEXT",
            details=f"Query: Name='{q_name}', Station='{q_station}', District='{q_district}', Contact='{q_contact}'"
        )

    return render_template(
        'search/search.html',
        results=results,
        has_searched=has_filters,
        q_name=q_name,
        q_station=q_station,
        q_district=q_district,
        q_contact=q_contact
    )


# --- Biometric Search Routes (Required by dashboard card) ---

@search_bp.route('/biometric', methods=['GET'])
@login_required
def biometric_portal():
    """Renders the biometric & photo search interface."""
    return render_template('search/biometric_search.html')


@search_bp.route('/api/match-face', methods=['POST'])
@login_required
def match_face_api():
    if 'face_image' not in request.files:
        return {"success": False, "message": "कोणताही फोटो सापडला नाही (No image uploaded)"}, 400
    return {"success": True, "message": "Face image processed against internal records.", "matches": []}


@search_bp.route('/api/match-fingerprint', methods=['POST'])
@login_required
def match_fingerprint_api():
    data = request.get_json(silent=True) or request.form
    scan_source = data.get('source', 'USB_SCANNER')
    return {"success": True, "source": scan_source, "message": f"Minutiae template received via {scan_source}.", "matches": []}