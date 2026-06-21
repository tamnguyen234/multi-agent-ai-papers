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
from app.db.models.digest import Digest, DigestPaper
from app.db.models.topic import Topic, PaperTopic
from app.db.models.audio import AudioAbstract
from app.services import storage_service

def is_demo_or_mock_paper(paper: Paper, project_root: Path) -> dict:
    """Classifies paper and returns classification reasons."""
    reasons = []
    title_lower = (paper.title or "").lower()
    
    if not paper.arxiv_id or not paper.arxiv_id.strip():
        reasons.append("Empty or missing arxiv_id")
        
    for kw in ["mock", "demo", "test", "sample", "dự phòng"]:
        if kw in title_lower:
            reasons.append(f"Title contains mock keyword: '{kw}'")
            break
            
    if not paper.pdf_path or not paper.pdf_path.strip():
        reasons.append("Empty pdf_path")
    else:
        pdf_path_on_disk = project_root / paper.pdf_path.lstrip("/")
        if not os.path.exists(pdf_path_on_disk):
            reasons.append(f"PDF file does not exist on disk: {paper.pdf_path}")
        elif os.path.getsize(pdf_path_on_disk) == 0:
            reasons.append(f"PDF file exists but is empty (0 bytes): {paper.pdf_path}")
            
    if paper.arxiv_url:
        if "arxiv.org" not in paper.arxiv_url.lower():
            reasons.append(f"Non-arXiv url domain: {paper.arxiv_url}")
            
    return {
        "is_mock": len(reasons) > 0,
        "reasons": reasons
    }

def main():
    print("=" * 70)
    print("DATABASE REAL DATA MODE VERIFICATION")
    print("=" * 70)

    db = SessionLocal()
    project_root = storage_service.get_project_root()
    failures = []

    try:
        # 1. Check Papers
        all_papers = db.query(Paper).all()
        mock_papers = []
        real_papers = []
        for p in all_papers:
            classif = is_demo_or_mock_paper(p, project_root)
            if classif["is_mock"]:
                mock_papers.append((p, classif["reasons"]))
            else:
                real_papers.append(p)

        print(f"Papers Audit:")
        print(f"  - Total Papers: {len(all_papers)}")
        print(f"  - Real Papers: {len(real_papers)} (Required: >= 100)")
        print(f"  - Mock Papers: {len(mock_papers)} (Required: 0)")

        if len(real_papers) < 100:
            failures.append(f"Real papers count is {len(real_papers)} which is less than 100.")
        if len(mock_papers) > 0:
            failures.append(f"Found {len(mock_papers)} mock/demo papers in the database:")
            for p, reasons in mock_papers[:5]:
                failures.append(f"    * ID {p.id}: Title: '{p.title[:50]}...' | Reasons: {', '.join(reasons)}")

        # 2. Check Digests
        all_digests = db.query(Digest).all()
        print(f"Digests Audit:")
        print(f"  - Total Digests: {len(all_digests)} (Required: >= 20)")

        if len(all_digests) < 20:
            failures.append(f"Digests count is {len(all_digests)} which is less than 20.")

        # Check digest paper counts
        digest_map = {d.id: d for d in all_digests}
        paper_ids = {p.id for p in all_papers}
        real_paper_ids = {p.id for p in real_papers}
        
        for d in all_digests:
            dps = db.query(DigestPaper).filter(DigestPaper.digest_id == d.id).all()
            # Verify exactly 5 papers, all must be real
            real_count = 0
            mock_count = 0
            orphan_count = 0
            for dp in dps:
                if dp.paper_id not in paper_ids:
                    orphan_count += 1
                elif dp.paper_id not in real_paper_ids:
                    mock_count += 1
                else:
                    real_count += 1
                    
            if len(dps) != 5 or real_count != 5:
                failures.append(
                    f"Digest ID {d.id} ({d.digest_date.strftime('%Y-%m-%d')}) has {len(dps)} relationships "
                    f"(Real: {real_count}, Mock: {mock_count}, Orphan: {orphan_count}). Expected exactly 5 real papers."
                )

        # 3. Check Topics
        all_topics = db.query(Topic).all()
        print(f"Topics Audit:")
        print(f"  - Total Topics: {len(all_topics)}")
        
        # Ensure no topic has 0 paper mapping
        empty_topics = []
        for t in all_topics:
            count = db.query(PaperTopic).filter(PaperTopic.topic_id == t.id).count()
            if count == 0:
                empty_topics.append(t)
                
        if empty_topics:
            failures.append(f"Found {len(empty_topics)} empty topics (topics with 0 papers mapping):")
            for t in empty_topics[:5]:
                failures.append(f"    * Topic ID {t.id}: '{t.name}'")

        # 4. Check Audio Abstracts
        all_audios = db.query(AudioAbstract).all()
        print(f"Audio Abstracts Audit:")
        print(f"  - Total Audio Abstracts: {len(all_audios)}")
        
        # Warnings for missing files on real papers (do not fail verification, just warn)
        missing_files = []
        for audio in all_audios:
            if audio.paper_id in real_paper_ids:
                if not audio.file_path:
                    missing_files.append((audio, "Empty file path in DB"))
                else:
                    path = project_root / audio.file_path.lstrip("/")
                    if not path.exists():
                        missing_files.append((audio, f"File missing on disk: {audio.file_path}"))
                    elif path.stat().st_size == 0:
                        missing_files.append((audio, f"File exists but is empty (0 bytes): {audio.file_path}"))
                        
        if missing_files:
            print("\n[WARNING] Audio Abstracts files missing for real papers:")
            for audio, msg in missing_files:
                print(f"  - ID {audio.id} (Paper {audio.paper_id}): {msg}")

        # Summary
        print("-" * 70)
        if failures:
            print(f"VERIFICATION FAILED: Found {len(failures)} issues.")
            for fail in failures:
                print(f"  - {fail}")
            sys.exit(1)
        else:
            print("VERIFICATION SUCCESSFUL: Database is in pure real-data mode and matches all safety requirements!")
            sys.exit(0)

    finally:
        db.close()

if __name__ == "__main__":
    main()
