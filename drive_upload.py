"""
ADVISIO — Google Drive Upload
===============================
Urcă un fișier PDF pe Google Drive într-un folder specific.
Returnează un link de download direct (nu de editare).
Configurare:
- GOOGLE_SERVICE_ACCOUNT_JSON → env var cu JSON-ul contului de serviciu (base64 sau raw)
- GOOGLE_DRIVE_PARENT_FOLDER → ID-ul folderului root "Advisio Audituri" din Drive
"""
import os, io, json, base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
SCOPES = ["https://www.googleapis.com/auth/drive"]
PARENT_FOLDER = os.environ.get("GOOGLE_DRIVE_PARENT_FOLDER", "")
def _get_service():
"""Construiește clientul Google Drive din env var."""
raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
if not raw:
raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON nu este setat în env vars.")
# Acceptă atât JSON raw cât și base64
try:
info = json.loads(raw)
except Exception:
info = json.loads(base64.b64decode(raw).decode())
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
return build("drive", "v3", credentials=creds, cache_discovery=False)
def _get_or_create_folder(service, folder_name, parent_id):
"""Găsește sau creează un subfolder în Drive."""
query = (
f"name='{folder_name}' and "
f"'{parent_id}' in parents and "
f"mimeType='application/vnd.google-apps.folder' and "
f"trashed=false"
)
results = service.files().list(q=query, fields="files(id, name)").execute()
files = results.get("files", [])
if files:
return files[0]["id"]
# Creează folderul
meta = {
"name": folder_name,
"mimeType": "application/vnd.google-apps.folder",
"parents": [parent_id],
}
folder = service.files().create(body=meta, fields="id").execute()
return folder["id"]
def upload_to_drive(pdf_bytes: bytes, filename: str, folder_name: str) -> str:
"""
Urcă pdf_bytes pe Google Drive.
Returnează un link direct de download (nu necesită autentificare — fișierul e public read).
"""
service = _get_service()
folder_id = _get_or_create_folder(service, folder_name, PARENT_FOLDER)
# Șterge versiunea veche dacă există (evită duplicate)
query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
old = service.files().list(q=query, fields="files(id)").execute().get("files", [])
for f in old:
service.files().delete(fileId=f["id"]).execute()
# Upload fișier nou
media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype="application/pdf", resumable=False)
meta = {"name": filename, "parents": [folder_id]}
file = service.files().create(body=meta, media_body=media, fields="id").execute()
file_id = file["id"]
# Setează permisiune publică (oricine cu link poate descărca)
service.permissions().create(
fileId=file_id,
body={"type": "anyone", "role": "reader"},
).execute()
# Returnează link direct de download
return f"https://drive.google.com/uc?export=download&id={file_id}"