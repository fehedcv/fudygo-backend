import firebase_admin
from firebase_admin import credentials, auth
import os
import json

firebase_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not firebase_service_account_json:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set.")

try:
    cred_json = json.loads(firebase_service_account_json)
    cred = credentials.Certificate(cred_json)
    firebase_admin.initialize_app(cred)
except json.JSONDecodeError:
    raise ValueError("Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON. Make sure it's a valid JSON string.")

