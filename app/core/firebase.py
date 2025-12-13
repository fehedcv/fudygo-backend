import firebase_admin
from firebase_admin import credentials, auth
import os
import json

_firebase_initialized = False

def init_firebase():
    global _firebase_initialized

    if _firebase_initialized:
        return

    firebase_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if not firebase_service_account_json:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set.")

    try:
        cred_json = json.loads(firebase_service_account_json)
        cred = credentials.Certificate(cred_json)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
    except json.JSONDecodeError:
        raise ValueError(
            "Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON. Must be single-line JSON with \\n in private_key."
        )
