"""File storage service for secure local/remote storage."""
import hashlib
import os
import shutil
from pathlib import Path
from typing import Tuple

# In-memory mock configuration (mimicking real S3/Local config)
UPLOAD_DIR = Path("uploads")
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def init_storage():
    """Ensure upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_file(file_content: bytes, original_filename: str, content_type: str) -> Tuple[str, str, int]:
    """
    Securely save an uploaded file.
    Validates size and type, hashes for deduplication/security, and saves securely.
    """
    init_storage()

    # 1. Size Validation
    file_size = len(file_content)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size {file_size} exceeds maximum {MAX_FILE_SIZE} bytes.")

    # 2. Type Validation (Basic header check - in production you'd use python-magic)
    # We enforce extension based on MIME type to avoid execution attacks
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type. Must be PDF or DOCX.")
    
    ext = ALLOWED_MIME_TYPES[content_type]

    # 3. Hash calculation (SHA-256)
    file_hash = hashlib.sha256(file_content).hexdigest()

    # 4. Save securely using content hash as name (prevents path traversal)
    secure_filename = f"{file_hash}{ext}"
    file_path = UPLOAD_DIR / secure_filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Return local path, hash, and size
    return str(file_path), file_hash, file_size
