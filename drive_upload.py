"""
ADVISIO — Supabase Storage Upload (înlocuiește Cloudinary)
===========================================================
Urcă un fișier PDF pe Supabase Storage și returnează un link public direct.

Configurare env vars în Railway:
- SUPABASE_URL         → https://xxxx.supabase.co
- SUPABASE_SERVICE_KEY → eyJ... (service_role key din Settings → API)

Bucket necesar în Supabase Storage:
- Nume: advisio-pdfs
- Public: ON
"""
import os
import requests

SUPABASE_URL         = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
BUCKET_NAME          = "advisio-pdfs"


def upload_to_drive(pdf_bytes: bytes, filename: str, folder_name: str) -> str:
    """
    Urcă pdf_bytes pe Supabase Storage.
    Returnează URL public direct (fără autentificare).
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL sau SUPABASE_SERVICE_KEY nu sunt setate în env vars.")

    # Construim calea fișierului în bucket
    safe_folder = "".join(c for c in folder_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
    safe_file   = filename if filename.endswith(".pdf") else filename + ".pdf"
    file_path   = f"{safe_folder}/{safe_file}"

    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_path}"

    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/pdf",
        "x-upsert": "true",   # suprascrie dacă există deja
    }

    response = requests.post(upload_url, data=pdf_bytes, headers=headers, timeout=60)

    if response.status_code not in (200, 201):
        raise ValueError(
            f"Supabase upload failed: HTTP {response.status_code} — {response.text[:200]}"
        )

    # URL public direct — funcționează pe orice device fără autentificare
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_path}"

    print(f"✓ Upload Supabase OK: {public_url}")
    return public_url
