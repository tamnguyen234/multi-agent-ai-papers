import os
import re
import time
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException, status

def get_project_root() -> Path:
    """Resolve the project root directory dynamically."""
    return Path(__file__).resolve().parents[3]

def ensure_dir(path: Path) -> None:
    """Ensure directory exists, create it recursively if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)

def build_dated_dir(base_dir: Path) -> Path:
    """Build dated directory path yyyy/mm/dd under base_dir."""
    today = datetime.now()
    date_path = Path(f"{today.strftime('%Y')}/{today.strftime('%m')}/{today.strftime('%d')}")
    full_path = base_dir / date_path
    ensure_dir(full_path)
    return full_path

def get_secure_filename(filename: str) -> str:
    """Sanitize the filename by removing path traversal patterns and keeping safe characters."""
    # Extract only the base name to strip path traversal attempts
    base_name = Path(filename).name
    
    # Split base name and extension
    name_parts = base_name.rsplit('.', 1)
    if len(name_parts) > 1:
        base, ext = name_parts[0], name_parts[1].lower()
    else:
        base, ext = base_name, ""
        
    # Standardize base name
    base = re.sub(r'[^a-zA-Z0-9_\-]', '_', base)
    base = base.strip('_')
    
    if not base:
        base = "file_" + uuid.uuid4().hex[:8]
        
    if ext:
        ext = re.sub(r'[^a-zA-Z0-9]', '', ext)
        return f"{base}.{ext}"
    return base

def make_unique_filename(target_dir: Path, secure_name: str) -> str:
    """Append a timestamp and short UUID if filename already exists to avoid overwriting."""
    if not (target_dir / secure_name).exists():
        return secure_name
        
    name_parts = secure_name.rsplit('.', 1)
    if len(name_parts) > 1:
        base, ext = name_parts[0], name_parts[1]
        suffix = f"_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        return f"{base}{suffix}.{ext}"
    else:
        suffix = f"_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        return f"{secure_name}{suffix}"

def save_upload_file(upload_file: UploadFile, target_dir: Path, filename: Optional[str] = None) -> Path:
    """Save upload_file using shutil.copyfileobj for stream-based writing."""
    original_name = filename or upload_file.filename or "uploaded_file"
    secured_name = get_secure_filename(original_name)
    final_name = make_unique_filename(target_dir, secured_name)
    
    target_file_path = target_dir / final_name
    ensure_dir(target_dir)
    
    # Write using file objects streaming
    upload_file.file.seek(0)
    with open(target_file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return target_file_path

def validate_extension(filename: str, allowed_extensions: list) -> None:
    """Validate file extension, raising 400 Bad Request if invalid."""
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no extension."
        )
    ext = f".{name_parts[1].lower()}"
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed extensions are: {', '.join(allowed_extensions)}"
        )

def save_paper_pdf(upload_file: UploadFile, filename: Optional[str] = None) -> str:
    """Validate extension and save paper PDF. Returns relative path with forward slashes."""
    orig_name = filename or upload_file.filename or ""
    validate_extension(orig_name, [".pdf"])
    
    base_dir = get_project_root() / "data" / "paper_pdf"
    dated_dir = build_dated_dir(base_dir)
    file_path = save_upload_file(upload_file, dated_dir, filename)
    
    rel_path = file_path.relative_to(get_project_root())
    return rel_path.as_posix()

def save_audio_abstract(upload_file: UploadFile, filename: Optional[str] = None) -> str:
    """Validate extension and save audio abstract. Returns relative path with forward slashes."""
    orig_name = filename or upload_file.filename or ""
    validate_extension(orig_name, [".wav", ".mp3", ".m4a"])
    
    base_dir = get_project_root() / "data" / "audio_abstract"
    dated_dir = build_dated_dir(base_dir)
    file_path = save_upload_file(upload_file, dated_dir, filename)
    
    rel_path = file_path.relative_to(get_project_root())
    return rel_path.as_posix()

def save_audio_chat_message(upload_file: UploadFile, filename: Optional[str] = None) -> str:
    """Validate extension and save audio chat message. Returns relative path with forward slashes."""
    orig_name = filename or upload_file.filename or ""
    validate_extension(orig_name, [".wav", ".mp3", ".m4a"])
    
    base_dir = get_project_root() / "data" / "audio_chat_message"
    dated_dir = build_dated_dir(base_dir)
    file_path = save_upload_file(upload_file, dated_dir, filename)
    
    rel_path = file_path.relative_to(get_project_root())
    return rel_path.as_posix()

def save_audio_chat_bytes(audio_bytes: bytes, extension: str = ".wav", prefix: str = "chat_tts") -> dict:
    """
    Generate a secure UUID filename internally, validate extension, protect against path traversal,
    save bytes to data/audio_chat_message/yyyy/mm/dd/ and return relative_path and url.
    """
    allowed_extensions = [".wav", ".mp3", ".ogg", ".m4a"]
    ext = extension.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed extensions are: {', '.join(allowed_extensions)}"
        )
        
    # Generate secure name internally
    secure_name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    
    base_dir = get_project_root() / "data" / "audio_chat_message"
    dated_dir = build_dated_dir(base_dir)
    
    # Target path resolution and path traversal check
    target_file_path = (dated_dir / secure_name).resolve()
    
    # Path traversal protection
    if not str(target_file_path).startswith(str(base_dir.resolve())):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected."
        )
        
    ensure_dir(dated_dir)
    
    with open(target_file_path, "wb") as f:
        f.write(audio_bytes)
        
    rel_path = target_file_path.relative_to(get_project_root())
    relative_path_str = rel_path.as_posix()
    
    return {
        "relative_path": relative_path_str,
        "url": path_to_url(relative_path_str)
    }

def save_paper_pdf_bytes(file_bytes: bytes, original_filename: str | None = None) -> dict:
    """
    Generate a secure UUID filename, validate extension is .pdf,
    protect against path traversal, save bytes to data/paper_pdf/yyyy/mm/dd/ and return
    relative_path, url, and size_bytes.
    """
    # Use UUID as filename to ensure uniqueness and avoid conflicts
    filename = f"paper_{uuid.uuid4().hex}.pdf"
    
    base_dir = get_project_root() / "data" / "paper_pdf"
    dated_dir = build_dated_dir(base_dir)
    
    # Target path resolution and path traversal check
    target_file_path = (dated_dir / filename).resolve()
    
    # Path traversal protection
    if not str(target_file_path).startswith(str(base_dir.resolve())):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected."
        )
        
    ensure_dir(dated_dir)
    
    with open(target_file_path, "wb") as f:
        f.write(file_bytes)
        
    rel_path = target_file_path.relative_to(get_project_root())
    relative_path_str = rel_path.as_posix()
    size_bytes = len(file_bytes)
    
    return {
        "relative_path": relative_path_str,
        "url": path_to_url(relative_path_str),
        "size_bytes": size_bytes
    }

def save_audio_abstract_bytes(audio_bytes: bytes, extension: str = ".wav", prefix: str = "abstract_tts") -> dict:
    """
    Generate a secure UUID filename internally, validate extension, protect against path traversal,
    save bytes to data/audio_abstract/yyyy/mm/dd/ and return relative_path and url.
    """
    allowed_extensions = [".wav", ".mp3", ".ogg", ".m4a"]
    ext = extension.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed extensions are: {', '.join(allowed_extensions)}"
        )
        
    # Generate secure name internally
    secure_name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    
    base_dir = get_project_root() / "data" / "audio_abstract"
    dated_dir = build_dated_dir(base_dir)
    
    # Target path resolution and path traversal check
    target_file_path = (dated_dir / secure_name).resolve()
    
    # Path traversal protection
    if not str(target_file_path).startswith(str(base_dir.resolve())):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected."
        )
        
    ensure_dir(dated_dir)
    
    with open(target_file_path, "wb") as f:
        f.write(audio_bytes)
        
    rel_path = target_file_path.relative_to(get_project_root())
    relative_path_str = rel_path.as_posix()
    
    return {
        "relative_path": relative_path_str,
        "url": path_to_url(relative_path_str)
    }

def path_to_url(relative_path: str) -> str:
    """Convert relative storage path to static URL path starting with /static/."""
    clean_path = relative_path.lstrip("/")
    return f"/static/{clean_path}"


