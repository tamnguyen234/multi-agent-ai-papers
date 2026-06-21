import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, date

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
from app.db.models.audio import AudioAbstract
from app.db.models.topic import Topic, PaperTopic

def main():
    parser = argparse.ArgumentParser(description="Verify database and filesystem consistency after backfill.")
    parser.add_argument("--days", type=int, default=20, help="Expected number of digest days.")
    parser.add_argument("--per-day", type=int, default=5, help="Expected papers per daily digest.")
    parser.add_argument("--check-audio", action="store_true", help="Check that audio files and records exist.")
    args = parser.parse_args()

    print("=" * 60)
    print("RUNNING BACKFILL DATA INTEGRITY VERIFICATION")
    print("=" * 60)
    print(f"Target check: {args.days} days, {args.per_day} papers/day")
    print(f"Check audio: {args.check_audio}")
    print("-" * 60)

    db = SessionLocal()
    project_root = Path(__file__).resolve().parents[2]

    errors = []
    warnings = []

    try:
        # 1. Verify Digest Count
        digests = db.query(Digest).order_by(Digest.digest_date.desc()).all()
        print(f"Found {len(digests)} total digests in database.")
        
        if len(digests) < args.days:
            errors.append(f"Digest count mismatch: Found {len(digests)} digests, expected at least {args.days}.")
        else:
            print(f"[OK] Digest count is sufficient (found {len(digests)} >= {args.days}).")

        # Get the latest N digests to inspect
        target_digests = digests[:args.days]
        
        all_paper_ids = set()
        all_arxiv_ids = set()

        print("\nVerifying each of the last digests:")
        for idx, d in enumerate(target_digests, 1):
            date_str = d.digest_date.strftime("%Y-%m-%d")
            print(f"  * Digest {idx}: Date {date_str} (ID: {d.id})")
            
            # Fetch papers for this digest
            dps = db.query(DigestPaper).filter(DigestPaper.digest_id == d.id).order_by(DigestPaper.rank_position).all()
            
            if len(dps) != args.per_day:
                errors.append(f"Digest {date_str} has {len(dps)} papers, expected exactly {args.per_day}.")
                continue
            
            # Verify ranks are exactly 1 to K
            ranks = [dp.rank_position for dp in dps]
            expected_ranks = list(range(1, args.per_day + 1))
            if ranks != expected_ranks:
                errors.append(f"Digest {date_str} rank positions are {ranks}, expected {expected_ranks}.")

            # Verify each paper
            for dp in dps:
                paper = dp.paper
                if not paper:
                    errors.append(f"Digest {date_str} has a missing paper relation for digest_paper ID {dp.id}.")
                    continue
                
                all_paper_ids.add(paper.id)
                all_arxiv_ids.add(paper.arxiv_id)

                # Verify metadata
                if not paper.arxiv_id:
                    errors.append(f"Paper ID {paper.id} has empty arxiv_id.")
                if not paper.title:
                    errors.append(f"Paper {paper.arxiv_id} has empty title.")
                if not paper.abstract:
                    errors.append(f"Paper {paper.arxiv_id} has empty abstract.")
                if not paper.published:
                    warnings.append(f"Paper {paper.arxiv_id} has empty published date.")
                if not paper.arxiv_url:
                    warnings.append(f"Paper {paper.arxiv_id} has empty arxiv_url.")
                
                # Resolve PDF path using project storage base / serving logic
                if not paper.pdf_path:
                    errors.append(f"Paper {paper.arxiv_id} has empty pdf_path.")
                else:
                    # Clean the path and make it absolute using project root
                    clean_pdf_path = paper.pdf_path.lstrip("/")
                    abs_pdf_path = project_root / clean_pdf_path
                    
                    if not abs_pdf_path.exists():
                        errors.append(f"Paper {paper.arxiv_id} PDF file does not exist at: {abs_pdf_path}")
                    elif abs_pdf_path.stat().st_size == 0:
                        errors.append(f"Paper {paper.arxiv_id} PDF file at {abs_pdf_path} is empty (0 bytes).")
                    else:
                        # Success verification
                        pass
                
                # Check pdf_url matches static serving endpoint expectation
                if paper.pdf_url:
                    if not (paper.pdf_url.startswith("/static/data/") or paper.pdf_url.startswith("/static/")):
                        errors.append(f"Paper {paper.arxiv_id} pdf_url '{paper.pdf_url}' does not start with /static/ prefix.")
                
                # Verify Audio if required
                if args.check_audio:
                    if not paper.has_audio:
                        errors.append(f"Paper {paper.arxiv_id} does not have has_audio set to True.")
                    
                    audio_rec = db.query(AudioAbstract).filter(AudioAbstract.paper_id == paper.id).first()
                    if not audio_rec:
                        errors.append(f"Paper {paper.arxiv_id} has no AudioAbstract record in database.")
                    elif not audio_rec.file_path:
                        errors.append(f"Paper {paper.arxiv_id} AudioAbstract record has empty file_path.")
                    else:
                        abs_audio_path = project_root / audio_rec.file_path.lstrip("/")
                        if not abs_audio_path.exists():
                            errors.append(f"Paper {paper.arxiv_id} audio file does not exist at: {abs_audio_path}")
                        elif abs_audio_path.stat().st_size == 0:
                            errors.append(f"Paper {paper.arxiv_id} audio file at {abs_audio_path} is empty (0 bytes).")

        print(f"\nTotal unique papers verified in this backfill: {len(all_paper_ids)}")
        print(f"Total unique arXiv IDs: {len(all_arxiv_ids)}")

        if len(all_arxiv_ids) < len(target_digests) * args.per_day:
            warnings.append(f"Deduplication picked some overlapping papers, unique arXiv IDs: {len(all_arxiv_ids)} vs expected {len(target_digests) * args.per_day}")

        # 2. Verify Topics & PaperTopics
        topics = db.query(Topic).all()
        print(f"\nFound {len(topics)} topics in database.")
        if not topics:
            warnings.append("No topics found in database. Trend analysis may not have run.")
        else:
            print("Topics detail:")
            for t in topics:
                paper_count = db.query(PaperTopic).filter(PaperTopic.topic_id == t.id).count()
                print(f"  * Topic: {t.name} ({paper_count} papers mapped)")
                
            pt_count = db.query(PaperTopic).count()
            print(f"Total PaperTopic mapping records: {pt_count}")
            if pt_count == 0:
                warnings.append("No paper-topic mappings found in paper_topics table.")

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
