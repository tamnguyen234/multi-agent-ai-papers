import os
import sys
import argparse
import time
from datetime import datetime
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
from app.services.audio_abstract_service import generate_audio_for_paper_summary
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
    parser = argparse.ArgumentParser(description="Generate missing audio abstracts for papers.")
    parser.add_argument("--all", action="store_true", help="Generate audio for all papers missing audio.")
    parser.add_argument("--limit", type=int, default=None, help="Limit maximum number of papers to process.")
    parser.add_argument("--paper-id", type=int, default=None, help="Process a specific paper by ID.")
    parser.add_argument("--voice", type=str, default="vi_female", help="Voice to use (vi_female | vi_male).")
    parser.add_argument("--language", type=str, default="vi", help="Language code (default: vi).")
    parser.add_argument("--dry-run", action="store_true", help="Dry run. Print candidates without calling TTS or saving to DB.")
    parser.add_argument("--sleep-seconds", type=float, default=2.0, help="Seconds to sleep between TTS requests.")
    parser.add_argument("--force", action="store_true", help="Force regenerate audio even if record/file exists.")
    parser.add_argument("--resume", action="store_true", help="Resume mode. Skip papers if their audio file already exists on disk.")
    
    args = parser.parse_args()

    # We must have either --all or --paper-id
    if not args.all and not args.paper_id:
        print("[ERROR] You must specify either --all or --paper-id <ID>.")
        sys.exit(1)

    db = SessionLocal()
    project_root = storage_service.get_project_root()

    try:
        # 1. Fetch papers
        query = db.query(Paper)
        if args.paper_id:
            query = query.filter(Paper.id == args.paper_id)
        papers = query.all()

        candidates = []
        pre_existing_count = 0
        skipped_count = 0

        # 2. Filter papers according to criteria
        for paper in papers:
            # Skip mock or demo papers
            if is_demo_or_mock_paper(paper):
                skipped_count += 1
                continue

            # Verify physical PDF exists on disk
            if not paper.pdf_path:
                skipped_count += 1
                continue
                
            pdf_path_on_disk = project_root / paper.pdf_path.lstrip("/")
            if not os.path.exists(pdf_path_on_disk) or os.path.getsize(pdf_path_on_disk) == 0:
                skipped_count += 1
                continue

            # Check existing audio record
            existing_audio = db.query(AudioAbstract).filter(AudioAbstract.paper_id == paper.id).first()
            audio_file_exists = False
            if existing_audio:
                audio_path_on_disk = project_root / existing_audio.file_path.lstrip("/")
                if os.path.exists(audio_path_on_disk) and os.path.getsize(audio_path_on_disk) > 0:
                    audio_file_exists = True

            if audio_file_exists:
                pre_existing_count += 1
                
                # If force is true, we process anyway
                if args.force:
                    candidates.append(paper)
                # If resume is true or force is false, we skip
                elif args.resume or not args.force:
                    continue
            else:
                # Missing audio file or record
                candidates.append(paper)

        print("=" * 60)
        print("AUDIO ABSTRACT BATCH GENERATOR")
        print("=" * 60)
        print(f"Total Papers Fetched: {len(papers)}")
        print(f"Skipped (Mock/Demo/No PDF): {skipped_count}")
        print(f"Pre-existing Audio Files: {pre_existing_count}")
        print(f"Candidates for Generation: {len(candidates)}")
        print(f"Dry Run Mode: {args.dry_run}")
        print(f"Limit: {args.limit}")
        print(f"Voice: {args.voice}")
        print("-" * 60)

        if not candidates:
            print("No candidate papers found for generation. Exiting.")
            return

        # Handle limit
        if args.limit is not None:
            candidates = candidates[:args.limit]
            print(f"Applied limit. Processing first {len(candidates)} papers.")

        if args.dry_run:
            print("\n[DRY RUN] Candidate papers listing:")
            for idx, p in enumerate(candidates, 1):
                print(f"  * Candidate {idx}: ID {p.id} | {p.arxiv_id} | {p.title[:60]}...")
            print(f"\n[DRY RUN] Would process {len(candidates)} papers.")
            return

        # Real run
        created_count = 0
        failed_count = 0
        error_list = []

        print("\nStarting generation process:")
        for idx, p in enumerate(candidates, 1):
            print(f"  [{idx}/{len(candidates)}] Processing paper ID {p.id} ({p.arxiv_id}) - {p.title[:50]}...")
            
            # Throttle between calls
            if idx > 1 and args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)
                
            try:
                # We reuse the same service layer function as the lazy generation endpoint
                res = generate_audio_for_paper_summary(
                    db=db,
                    paper=p,
                    force=args.force,
                    voice=args.voice,
                    language=args.language
                )
                print(f"    -> [SUCCESS] Mode: {res.get('mode')}. Audio URL: {res.get('audio_url')}")
                created_count += 1
            except Exception as pe:
                print(f"    -> [FAILED] Error: {pe}")
                failed_count += 1
                error_list.append((p.id, p.arxiv_id, str(pe)))

        # Summary Report
        print("\n" + "=" * 60)
        print("AUDIO ABSTRACT GENERATION SUMMARY REPORT")
        print("=" * 60)
        print(f"Real Papers Scanned: {len(papers) - skipped_count}")
        print(f"Pre-existing Audios: {pre_existing_count}")
        print(f"New Audios Created: {created_count}")
        print(f"Skipped / Resumed: {len(candidates) - created_count - failed_count}")
        print(f"Failed: {failed_count}")
        
        if error_list:
            print("\nGeneration Failures Detail:")
            for pid, aid, msg in error_list:
                print(f"  * Paper ID {pid} ({aid}): {msg}")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    main()
