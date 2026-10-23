import uuid
import os
import unicodedata
from datetime import datetime, date
from werkzeug.utils import secure_filename
from app.utils.image_handler import process_and_encode_image

def clean_text(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize('NFC', str(text).strip())

class SuspectProfile:
    @staticmethod
    def generate_profile_id(db):
        while True:
            unique_hex = uuid.uuid4().hex[:6].upper()
            year = datetime.utcnow().year
            profile_id = f"POL-{year}-{unique_hex}"
            if db is not None:
                if not db.profiles.find_one({"profile_id": profile_id}):
                    return profile_id
            else:
                return profile_id

    @staticmethod
    def validate_dob(dob_str: str) -> bool:
        if not dob_str:
            return True
        try:
            parsed_date = datetime.strptime(dob_str, "%Y-%m-%d").date()
            return parsed_date <= date.today()
        except ValueError:
            return False

    @staticmethod
    def build_profile_document(form_data, files, profile_id, current_officer):
        # 1. Main Photo (Compressed Base64 in Memory)
        main_photo_b64 = ""
        if 'main_photo' in files and files['main_photo'].filename != '':
            main_photo_b64 = process_and_encode_image(files['main_photo']) or ""

        # 2. Extra Photos (Compressed Base64 in Memory)
        extra_photos_b64 = []
        if 'extra_photos' in files:
            uploaded_files = files.getlist('extra_photos')
            for file in uploaded_files:
                if file.filename != '':
                    encoded_pic = process_and_encode_image(file)
                    if encoded_pic:
                        extra_photos_b64.append(encoded_pic)

        # 3. Dynamic Contacts
        contact_numbers = [clean_text(num) for num in form_data.getlist('contact_numbers[]') if num.strip()]

        # 4. Dynamic Sathidar (Associates)
        sathidar_names = form_data.getlist('sathidar_name[]')
        sathidar_numbers = form_data.getlist('sathidar_number[]')
        sathidar_addresses = form_data.getlist('sathidar_address[]')
        sathidar_list = []
        for name, num, addr in zip(sathidar_names, sathidar_numbers, sathidar_addresses):
            if name.strip():
                sathidar_list.append({
                    "name": clean_text(name),
                    "number": clean_text(num),
                    "address": clean_text(addr)
                })

        # 5. Multiple Gunha (Cases)
        fir_numbers = form_data.getlist('fir_number[]')
        sections_list = form_data.getlist('sections[]')
        details_list = form_data.getlist('case_other_details[]')
        cases_list = []
        for fir, sec, det in zip(fir_numbers, sections_list, details_list):
            if fir.strip() or sec.strip():
                cases_list.append({
                    "fir_number": clean_text(fir),
                    "sections": clean_text(sec),
                    "other_details": clean_text(det)
                })

        # 6. Biometric Thumbprint
        thumbprint_payload = form_data.get('biometric_thumb_data', '').strip()
        thumbprint_source = form_data.get('biometric_source', 'MANUAL').strip()

        # 7. Dynamic Custom Fields
        extra_keys = form_data.getlist('extra_key[]')
        extra_vals = form_data.getlist('extra_val[]')
        custom_fields = {}
        for k, v in zip(extra_keys, extra_vals):
            if k.strip():
                custom_fields[clean_text(k)] = clean_text(v)

        return {
            "profile_id": profile_id,
            "main_photo": main_photo_b64,
            "full_name": clean_text(form_data.get('full_name', '')),
            "alias": clean_text(form_data.get('alias', '')),
            "dob": form_data.get('dob', ''),
            "identification_mark": clean_text(form_data.get('identification_mark', '')),
            "biometric": {
                "source": thumbprint_source,
                "data": thumbprint_payload,
                "captured_at": datetime.utcnow() if thumbprint_payload else None
            },
            "station": clean_text(form_data.get('station', '')),
            "address": {
                "village_city": clean_text(form_data.get('village_city', '')),
                "subdist": clean_text(form_data.get('subdist', '')),
                "dist": clean_text(form_data.get('dist', ''))
            },
            "contacts": contact_numbers,
            "identity_docs": {
                "aadhaar_card_no": clean_text(form_data.get('aadhaar_card_no') or form_data.get('aadhaar_no', '')),
                "pan_card_no": clean_text(form_data.get('pan_card_no') or form_data.get('pan_no', '')).upper()
            },
            "sathidar": sathidar_list,
            "cases": cases_list,
            "extra_photos": extra_photos_b64,
            "tadipar": {
                "status": form_data.get('tadipar_status', 'No'),
                "order_details": clean_text(form_data.get('tadipar_details', ''))
            },
            "extra_details": clean_text(form_data.get('extra_details', '')),
            "custom_fields": custom_fields,
            "created_by": current_officer,
            "created_at": datetime.utcnow(),
            "last_modified_by": current_officer,
            "last_modified_at": datetime.utcnow()
        }