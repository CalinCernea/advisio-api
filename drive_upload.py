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
import cloudinary.api

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
        raise ValueError("CLOUDINARY_CLOUD_NAME nu este setat în env vars.")

    safe_folder = "".join(c for c in folder_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
    safe_file   = filename.replace(".pdf", "")

    # .pdf inclus în public_id — necesar pentru resource_type=raw
    public_id = f"advisio/{safe_folder}/{safe_file}.pdf"

    result = cloudinary.uploader.upload(
        pdf_bytes,
        public_id=public_id,
        resource_type="raw",
        type="upload",          # explicit "upload" = public by default
        overwrite=True,
        invalidate=True,        # invalidează CDN cache la overwrite
        access_mode="public",
    )

    # secure_url conține deja .pdf — nu mai adăugăm
    url = result["secure_url"]

    # fl_attachment forțează download în browser și pe iOS/Android
    # Înlocuim și eventualul /raw/upload/ cu versiunea cu fl_attachment

    print(f"✓ Upload Cloudinary OK: {url}")
    return url
