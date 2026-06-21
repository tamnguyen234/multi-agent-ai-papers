import os
from pathlib import Path
from fastapi import HTTPException, status
from app.config import settings

def resolve_pdf_path(pdf_path: str) -> Path:
    """
    Resolve relative pdf_path to the physical file under the project data folder.
    Guards against path traversal, absolute path injections, and verifies file exists.
    """
    if not pdf_path or not pdf_path.strip():
        raise ValueError("pdf_path is empty")
        
    path_str = pdf_path.strip()
    
    # Detect absolute paths
    # Absolute paths start with "/" or "\" or drive letter "C:" or UNC "//"
    if (
        path_str.startswith("/")
        or path_str.startswith("\\")
        or (len(path_str) > 1 and path_str[1] == ":" and path_str[0].isalpha())
        or path_str.startswith("//")
        or path_str.startswith("\\\\")
    ):
        # Normalize and check if it contains a drive letter
        cleaned = path_str.replace("\\", "/").strip("/")
        if len(cleaned) > 1 and cleaned[1] == ":" and cleaned[0].isalpha():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Absolute paths are not allowed."
            )
        if cleaned.startswith("//"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Absolute UNC paths are not allowed."
            )
        cleaned = "/" + cleaned
    else:
        cleaned = path_str.replace("\\", "/")
        
    # Standardize and clean slashes
    cleaned = cleaned.strip("/")
    
    # Check for path traversal patterns (.. or nested references)
    if ".." in cleaned or "/../" in cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected."
        )
        
    # Convert /static/data/paper_pdf/... or data/paper_pdf/... to relative path
    prefixes_to_strip = ["static/data/", "static/", "data/"]
    for prefix in prefixes_to_strip:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            
    # Now the path must start with "paper_pdf/"
    if not cleaned.startswith("paper_pdf/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid relative path format. Must start with paper_pdf/"
        )
        
    # Resolve against data dir
    data_dir = Path(settings.QA_DATA_DIR).resolve()
    target_path = (data_dir / cleaned).resolve()
    
    # Enforce that the target file resides strictly within the data/ directory
    if not str(target_path).startswith(str(data_dir)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt detected."
        )
        
    if not target_path.exists() or not target_path.is_file():
        raise FileNotFoundError(f"PDF file not found at resolved path: {target_path}")
        
    return target_path
