"""
ADVISIO — Cloudinary Upload
=======================================================
Urcă un fișier PDF pe Cloudinary și returnează un link direct de download.
Configurare env vars:
- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.utils

# Config Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
)


def upload_to_drive(pdf_bytes: bytes, filename: str, folder_name: str) -> str:
    """
    Urcă pdf_bytes pe Cloudinary.
    Returnează un link direct de download.
    """

    if not os.environ.get("CLOUDINARY_CLOUD_NAME"):
        raise ValueError("CLOUDINARY_CLOUD_NAME nu este setat.")

    # Curățare nume
    safe_folder = "".join(c for c in folder_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
    safe_file = filename.replace(".pdf", "").replace(".", "_")

    # ❗ FĂRĂ .pdf în public_id
    public_id = f"advisio/{safe_folder}/{safe_file}"

    # Upload
    result = cloudinary.uploader.upload(
        pdf_bytes,
        public_id=public_id,
        resource_type="raw",
        type="upload",
        overwrite=True,
        invalidate=True,
    )

    # Generare URL corect cu download (attachment)
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type="raw",
        secure=True,
        flags="attachment"
    )

    print(f"✓ Upload Cloudinary OK: {url}")
    return url
