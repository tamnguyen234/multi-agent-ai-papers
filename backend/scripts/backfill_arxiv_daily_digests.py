import os
import sys
import argparse
import time
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(backend_dir))

# Configure output encoding to support Vietnamese characters in console
if sys.platform == "win32":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", write_through=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", write_through=True)
    except Exception:
        pass

import requests

class HFAuthorCompat:
    def __init__(self, name):
        self.name = name

class HFPaperCompat:
    def __init__(self, item_dict):
        paper_dict = item_dict.get("paper", item_dict)
        self.entry_id = f"https://arxiv.org/abs/{paper_dict.get('id', '')}"
        self.title = paper_dict.get("title", "").replace('\n', ' ').strip()
        self.summary = paper_dict.get("summary", "").replace('\n', ' ').strip()
        self.authors = [HFAuthorCompat(a.get("name", "")) for a in paper_dict.get("authors", [])]
        
        pub_str = paper_dict.get("publishedAt", "")
        if pub_str:
            try:
                self.published = datetime.strptime(pub_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                self.published = datetime.now(timezone.utc)
        else:
            self.published = datetime.now(timezone.utc)
            
        self.primary_category = "cs.AI"
        self.categories = ["cs.AI"]
        self.upvotes = paper_dict.get("upvotes", 0)
from app.db.database import SessionLocal
from app.db.models.paper import Paper
from app.db.models.digest import Digest, DigestPaper
from app.db.models.audio import AudioAbstract
from app.db.models.topic import Topic, PaperTopic

def generate_extractive_summary(abstract: str, max_sentences: int = 3, max_chars: int = 400) -> str:
    """Disabled paper summarization. Returns empty string."""
    return ""

def calculate_paper_score(title: str, abstract: str, primary_cat: str, categories: list, published_dt, target_date) -> float:
    CATEGORY_WEIGHTS = {
        "cs.AI": 1.0,
        "cs.CL": 1.0,
        "cs.LG": 1.0,
        "cs.CV": 0.8,
        "cs.RO": 0.7,
        "cs.SD": 0.7
    }
    TRENDING_KEYWORDS = [
        "llm", "large language model", "transformer", "prompt", "gpt", "llama", "deepseek", "qwen",
        "rag", "retrieval", "vector database", "embedding", "faiss", "document qa",
        "agent", "multi-agent", "autonomous agent", "workflow", "coordination",
        "safety", "alignment", "hallucination", "bias", "robustness", "trustworthy",
        "reasoning", "chain of thought", "mathematical",
        "diffusion", "image generation", "computer vision",
        "speech", "audio", "tts", "text-to-speech", "whisper",
        "robot", "robotics"
    ]
    age_days = abs((published_dt.date() - target_date).days)
    recency_score = 1.0 / (1.0 + age_days)
    cat_weight = CATEGORY_WEIGHTS.get(primary_cat, 0.5)
    text = f"{title} {abstract}".lower()
    keyword_matches = sum(1 for kw in TRENDING_KEYWORDS if kw in text)
    keyword_boost = min(0.3, keyword_matches * 0.05)
    multi_cat_boost = 0.05 if len(categories) > 1 else 0.0
    final_score = (recency_score * 0.4) + (cat_weight * 0.3) + keyword_boost + multi_cat_boost
    return round(min(0.99, max(0.10, final_score)), 2)

def get_papers_for_date(target_date: date, used_ids: set, sleep_seconds: float, global_pool: list) -> list:
    date_str = target_date.strftime("%Y-%m-%d")
    print(f"  [HuggingFace] Querying Daily Papers for date {date_str}...")
    
    try:
        r = requests.get(f"https://huggingface.co/api/daily_papers?date={date_str}", timeout=15)
        if r.status_code == 200:
            results = r.json()
        else:
            print(f"  [HuggingFace] Query failed for date {date_str} with status {r.status_code}")
            results = []
    except Exception as e:
        print(f"  [HuggingFace] Query failed for date {date_str}: {e}")
        results = []
        
    papers = []
    for item in results:
        paper_dict = item.get("paper", item)
        clean_id = paper_dict.get("id", "")
        if not clean_id or clean_id in used_ids:
            continue
        papers.append(HFPaperCompat(item))
        
    if len(papers) >= 5:
        selected_results = papers[:5]
        time.sleep(sleep_seconds)
        return selected_results
        
    # Fallback to pre-fetched pool
    print(f"  [HuggingFace] Only found {len(papers)} unique papers for date {date_str}. Falling back to pre-fetched pool...")
    available_results = []
    for r in global_pool:
        raw_id = r.entry_id.split('/abs/')[-1]
        clean_id = raw_id
        if clean_id not in used_ids and clean_id not in [p.entry_id.split('/abs/')[-1] for p in papers]:
            available_results.append(r)
            
    # Sort remaining available results by proximity to target_date
    def distance_to_date(r):
        pub_dt = r.published
        pub_date = pub_dt.date() if isinstance(pub_dt, datetime) else pub_dt
        return abs((pub_date - target_date).days)
        
    available_results.sort(key=distance_to_date)
    
    needed = 5 - len(papers)
    supplement = available_results[:needed]
    papers.extend(supplement)
    
    time.sleep(sleep_seconds)
    return papers[:5]


def main():
    parser = argparse.ArgumentParser(description="Backfill arXiv daily digests for testing.")
    parser.add_argument("--days", type=int, default=20, help="Number of days to backfill.")
    parser.add_argument("--per-day", type=int, default=5, help="Number of papers per day.")
    parser.add_argument("--start-date", type=str, default=None, help="Start date in YYYY-MM-DD format (default: today).")
    parser.add_argument("--force", action="store_true", help="Force rebuild digests and overwrite rankings.")
    parser.add_argument("--force-trends", action="store_true", help="Delete all existing topics and paper_topics before running trend analyze.")
    parser.add_argument("--generate-audio", action="store_true", help="Generate audio abstract for papers using TTS Agent.")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode. Do not write to database or download files.")
    parser.add_argument("--sleep-seconds", type=float, default=3.0, help="Sleep duration between arXiv requests.")
    parser.add_argument("--send-email", action="store_true", help="Send email notifications (requires --confirm-send-email).")
    parser.add_argument("--confirm-send-email", action="store_true", help="Confirmation flag for sending emails.")
    args = parser.parse_args()

    # Verify email flags
    if args.send_email and not args.confirm_send_email:
        print("[ERROR] To send emails, you must specify both --send-email and --confirm-send-email.")
        sys.exit(1)

    # Determine start date
    if args.start_date:
        try:
            start_date_obj = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"[ERROR] Start date must be in YYYY-MM-DD format: {args.start_date}")
            sys.exit(1)
    else:
        start_date_obj = datetime.now().date()

    print(f"Starting arXiv backfill process:")
    print(f"  Days: {args.days}")
    print(f"  Papers per day: {args.per_day}")
    print(f"  Start date: {start_date_obj}")
    print(f"  Force rebuild: {args.force}")
    print(f"  Generate audio: {args.generate_audio}")
    print(f"  Dry run: {args.dry_run}")
    print(f"  Sleep seconds: {args.sleep_seconds}")
    print(f"  Send email: {args.send_email}")

    db = SessionLocal()
    
    # Track used paper IDs
    used_arxiv_ids = set()
    existing_papers = db.query(Paper.arxiv_id).all()
    used_arxiv_ids.update([p[0] for p in existing_papers])

    # Pre-fetch large pool
    print("[HuggingFace] Pre-fetching a pool of recent daily papers for fallback...")
    try:
        r = requests.get("https://huggingface.co/api/daily_papers", params={"limit": 50}, timeout=15)
        if r.status_code == 200:
            global_fallback_pool = [HFPaperCompat(p) for p in r.json()]
            print(f"[HuggingFace] Pre-fetched {len(global_fallback_pool)} papers for fallback pool.")
        else:
            print(f"[WARNING] Pre-fetch failed with status: {r.status_code}. Will try fetching per-day.")
            global_fallback_pool = []
    except Exception as e:
        print(f"[WARNING] Pre-fetch failed: {e}. Will try fetching per-day.")
        global_fallback_pool = []

    # Process metrics
    total_days = 0
    total_papers_expected = args.days * args.per_day
    total_papers_saved = 0
    total_digests_created_or_reused = 0
    total_pdfs_downloaded = 0
    total_failures = 0
    error_list = []

    # Loop through days going backwards
    for d in range(args.days):
        target_date = start_date_obj - timedelta(days=d)
        date_str = target_date.strftime("%Y-%m-%d")
        print(f"\nProcessing Day {d + 1}/{args.days}: {date_str}")
        
        # Check if digest already exists
        digest = db.query(Digest).filter(Digest.digest_date == target_date).first()
        if digest and not args.force:
            print(f"  [Digest] Digest for {date_str} already exists. Skipping...")
            total_digests_created_or_reused += 1
            # Still retrieve unique paper IDs already associated to mark them as used
            dps = db.query(DigestPaper).filter(DigestPaper.digest_id == digest.id).all()
            for dp in dps:
                used_arxiv_ids.add(dp.paper.arxiv_id)
            continue
            
        # Get papers for target date
        results = get_papers_for_date(target_date, used_arxiv_ids, args.sleep_seconds, global_fallback_pool)
        
        if len(results) < args.per_day:
            print(f"  [WARNING] Only found {len(results)} papers for {date_str} (expected {args.per_day}).")
            
        if args.dry_run:
            print(f"  [DRY RUN] Selected papers for {date_str}:")
            for idx, r in enumerate(results, 1):
                raw_id = r.entry_id.split('/abs/')[-1]
                print(f"    Rank {idx}: {raw_id} - {r.title[:60]}...")
                used_arxiv_ids.add(raw_id)
            total_digests_created_or_reused += 1
            total_days += 1
            continue

        # Real Mode: Save to Database
        try:
            # Get or create digest
            if not digest:
                digest = Digest(digest_date=target_date)
                db.add(digest)
                db.flush()
                total_digests_created_or_reused += 1
            else:
                # Force mode: Delete old rankings
                db.query(DigestPaper).filter(DigestPaper.digest_id == digest.id).delete()
                db.commit()
                db.refresh(digest)

            # Score results relative to target date
            scored_results = []
            for r in results:
                raw_id = r.entry_id.split('/abs/')[-1]
                clean_id = raw_id
                
                # Normalize category names
                primary_cat = r.primary_category
                categories = r.categories
                
                score = calculate_paper_score(r.title, r.summary, primary_cat, categories, r.published, target_date)
                scored_results.append((score, r))
                
            # Sort scored results
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Upsert papers
            for rank, (score, r) in enumerate(scored_results, 1):
                raw_id = r.entry_id.split('/abs/')[-1]
                clean_id = raw_id
                
                # Check if paper already exists in database
                paper = db.query(Paper).filter(Paper.arxiv_id == clean_id).first()
                
                # Parse published date string
                pub_date = r.published.date() if isinstance(r.published, datetime) else r.published
                
                authors = [auth.name for auth in r.authors]
                summary = generate_extractive_summary(r.summary)
                
                # Auto-translate summary and abstract to Vietnamese on ingestion
                from app.services.tts_client import translate_text
                summary_vi = None
                if summary:
                    try:
                        summary_vi = translate_text(summary)["translated_text"]
                    except Exception as te:
                        print(f"    [WARNING] Failed to auto-translate summary for {clean_id}: {te}")
                        
                abstract_vi = None
                if r.summary:
                    try:
                        abstract_vi = translate_text(r.summary)["translated_text"]
                    except Exception as te:
                        print(f"    [WARNING] Failed to auto-translate abstract for {clean_id}: {te}")

                if not paper:
                    paper = Paper(
                        arxiv_id=clean_id,
                        title=r.title.replace('\n', ' ').strip(),
                        abstract=r.summary.replace('\n', ' ').strip(),
                        summary=summary,
                        summary_vi=summary_vi,
                        abstract_vi=abstract_vi,
                        authors=authors,
                        published=pub_date,
                        score=score,
                        upvotes=r.upvotes,
                        arxiv_url=r.entry_id,
                        source="huggingface",
                        has_audio=False
                    )
                    db.add(paper)
                    db.flush()
                    total_papers_saved += 1
                else:
                    # Update metadata
                    paper.title = r.title.replace('\n', ' ').strip()
                    paper.abstract = r.summary.replace('\n', ' ').strip()
                    paper.summary = summary
                    paper.summary_vi = summary_vi
                    paper.abstract_vi = abstract_vi
                    paper.authors = authors
                    paper.published = pub_date
                    paper.score = score
                    paper.upvotes = r.upvotes
                    paper.arxiv_url = r.entry_id
                    paper.source = "huggingface"
                    db.flush()
                    
                used_arxiv_ids.add(clean_id)
                
                # Associate digest paper ranking
                dp = DigestPaper(
                    digest_id=digest.id,
                    paper_id=paper.id,
                    rank_position=rank
                )
                db.add(dp)
                db.flush()
                
                # Download PDF
                from app.services.pdf_download_service import download_and_attach_pdf
                try:
                    pdf_res = download_and_attach_pdf(db, paper.id)
                    if pdf_res.get("mode") == "downloaded":
                        total_pdfs_downloaded += 1
                except Exception as pdf_err:
                    print(f"    [WARNING] PDF download failed for paper {clean_id}: {pdf_err}")
                    
                # Generate Audio Abstract if enabled
                if args.generate_audio:
                    from app.services.audio_abstract_service import generate_audio_for_paper_summary
                    try:
                        generate_audio_for_paper_summary(db, paper, force=args.force)
                    except Exception as audio_err:
                        print(f"    [WARNING] TTS generation failed for paper {clean_id}: {audio_err}")

            db.commit()
            print(f"  [Digest] Digest and {len(scored_results)} papers successfully saved for {date_str}.")
            total_days += 1

            # Trigger email notifications if enabled
            if args.send_email:
                try:
                    from app.services.notification_service import NotificationService
                    print(f"  [Email] Sending digest notifications for {date_str}...")
                    NotificationService.send_daily_digest_notifications(db, digest)
                except Exception as email_err:
                    print(f"  [WARNING] Email notification failed: {email_err}")

        except Exception as day_err:
            db.rollback()
            print(f"  [ERROR] Day processing failed for {date_str}: {day_err}")
            total_failures += 1
            error_list.append((date_str, str(day_err)))

    # Force delete existing trends if force-trends flag is set
    if not args.dry_run and args.force_trends:
        print("\n[Trends] Force trends flag is enabled. Deleting existing topics and paper_topics...")
        db.query(PaperTopic).delete()
        db.query(Topic).delete()
        db.commit()

    # Trigger Trend Analysis at the end
    if not args.dry_run:
        try:
            from app.services.trend_service import analyze_and_store_trends
            print("\n[Trends] Running trend topic analysis on all saved papers...")
            trend_res = analyze_and_store_trends(db)
            print(f"[Trends] Complete. Found {trend_res.get('topic_count', 0)} topics mapped across {trend_res.get('total_papers', 0)} papers.")
        except Exception as trend_err:
            print(f"\n[WARNING] Trend analysis execution failed: {trend_err}")

    db.close()

    # Print summary reports
    print("\n" + "=" * 60)
    print("BACKFILL JOB SUMMARY REPORT")
    print("=" * 60)
    print(f"Total Days Processed: {total_days}")
    print(f"Expected Paper Mappings: {total_papers_expected}")
    print(f"Total New Papers Saved: {total_papers_saved}")
    print(f"Total Digests Created/Reused: {total_digests_created_or_reused}")
    print(f"Total PDFs Downloaded: {total_pdfs_downloaded}")
    print(f"Total Daily Failures: {total_failures}")
    if error_list:
        print("\nFailures Detail:")
        for err_date, err_msg in error_list:
            print(f"  * {err_date}: {err_msg}")
    print("=" * 60)

if __name__ == "__main__":
    main()
