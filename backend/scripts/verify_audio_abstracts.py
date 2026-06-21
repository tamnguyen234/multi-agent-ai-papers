import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(backend_dir))

# Configure output encoding to support Vietnamese characters in console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", write_through=True)

from app.db.database import SessionLocal
from app.db.models.paper import Paper
from app.db.models.audio import AudioAbstract
from app.services import storage_service

def is_demo_or_mock_paper(paper: Paper) -> bool:
    """Check if the paper is a mock, demo, or sample paper."""
    title_lower = (paper.title or "").lower()
    if not paper.arxiv_id or not paper.arxiv_id.strip():
        return True
    for kw in ["mock", "demo", "test", "sample", "dự phòng"]:
        if kw in title_lower:
            return True
    return False

def main():
    print("=" * 60)
    print("RUNNING AUDIO ABSTRACT DATA INTEGRITY VERIFICATION")
    print("=" * 60)

    db = SessionLocal()
    project_root = storage_service.get_project_root()

    errors = []
    warnings = []

    try:
        # 1. Fetch all papers
        papers = db.query(Paper).all()
        
        # Filter real vs mock/demo
        real_papers = [p for p in papers if not is_demo_or_mock_paper(p)]
        mock_papers = [p for p in papers if is_demo_or_mock_paper(p)]
        
        print(f"Total Papers in Database: {len(papers)}")
        print(f"  * Real Papers: {len(real_papers)}")
        print(f"  * Mock/Demo Papers: {len(mock_papers)}")

        # 2. Check for duplicate audio records by paper_id at application level
        from sqlalchemy import func
        duplicates = (
            db.query(AudioAbstract.paper_id, func.count(AudioAbstract.id))
            .group_by(AudioAbstract.paper_id)
            .having(func.count(AudioAbstract.id) > 1)
            .all()
        )
        if duplicates:
            for pid, count in duplicates:
                errors.append(f"Duplicate AudioAbstract records found for Paper ID {pid}: mapped {count} times.")
        else:
            print("[OK] No duplicate AudioAbstract records found by paper_id.")

        # 3. Analyze audio abstract integrity for real papers
        real_with_audio_record = 0
        real_missing_audio_record = 0
        audio_files_existing_on_disk = 0
        broken_audio_paths_in_db = 0

        print("\nAnalyzing Real Papers:")
        for paper in real_papers:
            # Query audio abstract
            audio = db.query(AudioAbstract).filter(AudioAbstract.paper_id == paper.id).first()
            
            if audio:
                real_with_audio_record += 1
                
                # Check physical file on disk
                if not audio.file_path:
                    errors.append(f"Paper {paper.arxiv_id} (ID: {paper.id}) has AudioAbstract record with empty file_path.")
                    broken_audio_paths_in_db += 1
                    continue
                    
                abs_audio_path = project_root / audio.file_path.lstrip("/")
                if not abs_audio_path.exists():
                    errors.append(f"Paper {paper.arxiv_id} (ID: {paper.id}) audio file missing on disk: {abs_audio_path}")
                    broken_audio_paths_in_db += 1
                elif abs_audio_path.stat().st_size == 0:
                    errors.append(f"Paper {paper.arxiv_id} (ID: {paper.id}) audio file exists but is empty (0 bytes): {abs_audio_path}")
                    broken_audio_paths_in_db += 1
                else:
                    audio_files_existing_on_disk += 1
            else:
                real_missing_audio_record += 1

        print(f"  * Real Papers with Audio record in DB: {real_with_audio_record}")
        print(f"  * Real Papers missing Audio record: {real_missing_audio_record}")
        print(f"  * Valid Audio Files on disk: {audio_files_existing_on_disk}")
        print(f"  * Broken / Missing Audio Files: {broken_audio_paths_in_db}")

        # 4. Verify no audio abstracts exist for mock/demo papers
        mock_with_audio = 0
        for paper in mock_papers:
            audio = db.query(AudioAbstract).filter(AudioAbstract.paper_id == paper.id).first()
            if audio:
                mock_with_audio += 1
                warnings.append(f"Mock/Demo Paper ID {paper.id} has an AudioAbstract record (Path: {audio.file_path}).")
        if mock_with_audio > 0:
            print(f"[WARN] Found {mock_with_audio} mock/demo papers with associated audio abstract records.")
        else:
            print("[OK] No mock/demo papers have audio abstract records.")

    except Exception as e:
        errors.append(f"Database error during verification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Errors: {len(errors)}")
    print(f"Total Warnings: {len(warnings)}")
    
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [WARN] {w}")
            
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  [ERROR] {e}")
        print("\n[FAILED] Verification completed with errors. Consistency checks failed.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Verification completed successfully! All records and files are consistent.")
        sys.exit(0)

if __name__ == "__main__":
    main()
