"""
ADVISIO — Cloudinary Upload (înlocuiește Google Drive)
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

    # Nume unic pentru fișier bazat pe folder + filename
    safe_folder = "".join(c for c in folder_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
    safe_file   = filename.replace(".pdf", "")
    public_id   = f"advisio/{safe_folder}/{safe_file}"

    result = cloudinary.uploader.upload(
        pdf_bytes,
        public_id=public_id,
        resource_type="raw",      # necesar pentru PDF
        overwrite=True,           # suprascrie versiunea veche
        access_mode="public",
    )

    return result["secure_url"] + ".pdf"
