import os
import sys
from pathlib import Path
from datetime import datetime

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
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.notification import Notification
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
    print("DATABASE DATA AUDIT & VALIDATION REPORT")
    print("=" * 70)

    db = SessionLocal()
    project_root = storage_service.get_project_root()

    try:
        # 1. Auditing Papers
        all_papers = db.query(Paper).all()
        real_papers = []
        mock_papers = []
        
        for p in all_papers:
            classif = is_demo_or_mock_paper(p, project_root)
            if classif["is_mock"]:
                mock_papers.append((p, classif["reasons"]))
            else:
                real_papers.append(p)
                
        # 2. Auditing Digests & Digest Papers
        all_digests = db.query(Digest).all()
        digest_stats = []
        orphan_digest_papers = []
        mock_digest_papers = []
        
        # Build map of paper existence & mock status
        paper_map = {p.id: p for p in all_papers}
        mock_paper_ids = {p.id for p, _ in mock_papers}
        
        for d in all_digests:
            dps = db.query(DigestPaper).filter(DigestPaper.digest_id == d.id).all()
            d_mock_count = 0
            d_orphan_count = 0
            d_real_count = 0
            
            for dp in dps:
                if dp.paper_id not in paper_map:
                    d_orphan_count += 1
                    orphan_digest_papers.append(dp)
                elif dp.paper_id in mock_paper_ids:
                    d_mock_count += 1
                    mock_digest_papers.append(dp)
                else:
                    d_real_count += 1
                    
            digest_stats.append({
                "digest": d,
                "total": len(dps),
                "real": d_real_count,
                "mock": d_mock_count,
                "orphan": d_orphan_count
            })

        # 3. Auditing Topics & Paper Topics
        all_topics = db.query(Topic).all()
        all_pts = db.query(PaperTopic).all()
        
        orphan_pts = []
        mock_pts = []
        real_pts = []
        
        for pt in all_pts:
            if pt.paper_id not in paper_map:
                orphan_pts.append(pt)
            elif pt.paper_id in mock_paper_ids:
                mock_pts.append(pt)
            else:
                real_pts.append(pt)
                
        # Topics check: topics with zero real paper mappings
        topics_with_real_count = {}
        for t in all_topics:
            count = db.query(PaperTopic).filter(
                PaperTopic.topic_id == t.id,
                PaperTopic.paper_id.notin_(list(mock_paper_ids) + [0])
            ).count()
            topics_with_real_count[t.id] = count

        # 4. Auditing Audio Abstracts
        all_audios = db.query(AudioAbstract).all()
        real_audios = []
        orphan_audios = []
        mock_audios = []
        missing_file_audios = []
        
        # For duplicates checking
        audio_by_paper_id = {}
        duplicate_audios = []
        
        for audio in all_audios:
            # Check duplicate
            if audio.paper_id in audio_by_paper_id:
                duplicate_audios.append(audio)
            else:
                audio_by_paper_id[audio.paper_id] = audio
                
            if audio.paper_id not in paper_map:
                orphan_audios.append(audio)
            elif audio.paper_id in mock_paper_ids:
                mock_audios.append(audio)
            else:
                # Real paper mapping
                # Check file existence
                if not audio.file_path:
                    missing_file_audios.append((audio, "Empty file_path in database"))
                else:
                    audio_path_on_disk = project_root / audio.file_path.lstrip("/")
                    if not os.path.exists(audio_path_on_disk):
                        missing_file_audios.append((audio, f"File missing on disk: {audio.file_path}"))
                    elif os.path.getsize(audio_path_on_disk) == 0:
                        missing_file_audios.append((audio, f"File exists but is empty: {audio.file_path}"))
                    else:
                        real_audios.append(audio)

        # 5. Auditing Chats
        all_sessions = db.query(ChatSession).all()
        all_messages = db.query(ChatMessage).all()
        
        demo_sessions = []
        demo_messages_count = 0
        
        for sess in all_sessions:
            is_demo = sess.paper_id in mock_paper_ids
            # If not yet flagged, check if any of its message contents contains mock keywords
            if not is_demo:
                msgs = db.query(ChatMessage).filter(ChatMessage.chat_session_id == sess.id).all()
                for m in msgs:
                    content_lower = (m.content or "").lower()
                    for kw in ["mock", "demo", "test", "sample", "thử nghiệm"]:
                        if kw in content_lower:
                            is_demo = True
                            break
                    if is_demo:
                        break
                
            if is_demo:
                demo_sessions.append(sess)
                msg_count = db.query(ChatMessage).filter(ChatMessage.chat_session_id == sess.id).count()
                demo_messages_count += msg_count

        # 6. Auditing Notifications
        all_notis = db.query(Notification).all()
        orphan_notis = []
        for n in all_notis:
            if n.digest_id and n.digest_id not in [d.id for d in all_digests]:
                orphan_notis.append(n)

        # Print audit summary tables
        print("\nSUMMARY STATS:")
        print("-" * 70)
        print(f"{'Table/Component':<25} | {'Total':<8} | {'Real/Valid':<12} | {'Mock/Demo':<10} | {'Orphans':<8}")
        print("-" * 70)
        print(f"{'Papers':<25} | {len(all_papers):<8} | {len(real_papers):<12} | {len(mock_papers):<10} | {0:<8}")
        print(f"{'Digests':<25} | {len(all_digests):<8} | {sum(1 for s in digest_stats if s['real'] == 5):<12} | {0:<10} | {0:<8}")
        print(f"{'Digest Papers':<25} | {db.query(DigestPaper).count():<8} | {db.query(DigestPaper).count() - len(mock_digest_papers) - len(orphan_digest_papers):<12} | {len(mock_digest_papers):<10} | {len(orphan_digest_papers):<8}")
        print(f"{'Topics':<25} | {len(all_topics):<8} | {sum(1 for tid, c in topics_with_real_count.items() if c > 0):<12} | {0:<10} | {sum(1 for tid, c in topics_with_real_count.items() if c == 0):<8}")
        print(f"{'Paper Topics':<25} | {len(all_pts):<8} | {len(real_pts):<12} | {len(mock_pts):<10} | {len(orphan_pts):<8}")
        print(f"{'Audio Abstracts':<25} | {len(all_audios):<8} | {len(real_audios):<12} | {len(mock_audios):<10} | {len(orphan_audios):<8}")
        print(f"{'Chat Sessions':<25} | {len(all_sessions):<8} | {len(all_sessions) - len(demo_sessions):<12} | {len(demo_sessions):<10} | {0:<8}")
        print("-" * 70)

        # Print Details of issues
        if mock_papers:
            print(f"\n[Mock Papers Details] Found {len(mock_papers)} mock/demo papers:")
            for p, r in mock_papers[:15]:
                print(f"  * ID {p.id}: Title: '{p.title[:50]}...' | Reasons: {', '.join(r)}")
            if len(mock_papers) > 15:
                print(f"  ... and {len(mock_papers) - 15} more.")

        # Incomplete Digests
        incomplete_digests = [s for s in digest_stats if s["real"] != 5]
        if incomplete_digests:
            print(f"\n[Incomplete Digests Details] Found {len(incomplete_digests)} digests without exactly 5 real papers:")
            for item in incomplete_digests:
                date_str = item["digest"].digest_date.strftime("%Y-%m-%d")
                print(f"  * Date: {date_str} (ID: {item['digest'].id}) - Real papers: {item['real']}, Mock: {item['mock']}, Orphan: {item['orphan']}")

        # Topics mapping issues
        empty_topics = [t for t in all_topics if topics_with_real_count[t.id] == 0]
        if empty_topics:
            print(f"\n[Empty Topics Details] Found {len(empty_topics)} topics mapping to zero real papers:")
            for t in empty_topics:
                print(f"  * Topic ID {t.id}: '{t.name}'")

        # Audio missing files
        if missing_file_audios:
            print(f"\n[Audio Abstracts Warnings] Found {len(missing_file_audios)} records for real papers with missing/empty files:")
            for audio, msg in missing_file_audios:
                p = paper_map.get(audio.paper_id)
                p_title = p.title[:40] if p else "Unknown Paper"
                print(f"  * ID {audio.id} (Paper {audio.paper_id} - '{p_title}...'): {msg}")

        if duplicate_audios:
            print(f"\n[Audio Abstracts Warnings] Found {len(duplicate_audios)} duplicate mapping records:")
            for audio in duplicate_audios:
                print(f"  * ID {audio.id} duplicates mapping for Paper ID {audio.paper_id}")

        # Chat details
        if demo_sessions:
            print(f"\n[Demo Chat Sessions Details] Found {len(demo_sessions)} demo/test chat sessions:")
            for sess in demo_sessions[:10]:
                print(f"  * ID {sess.id}: User ID: {sess.user_id} | Paper ID: {sess.paper_id}")
            if len(demo_sessions) > 10:
                print(f"  ... and {len(demo_sessions) - 10} more.")

        # Summary recommendations
        print("\nCLEANUP RECOMMENDATIONS:")
        print("-" * 70)
        print(f"  1. Delete {len(mock_papers)} mock/demo papers.")
        print(f"  2. Delete {len(mock_digest_papers)} mock digest_papers relationships.")
        print(f"  3. Delete {len(orphan_digest_papers)} orphan digest_papers relationships.")
        print(f"  4. Delete {len(mock_pts) + len(orphan_pts)} mock/orphan paper_topics relationships.")
        print(f"  5. Delete {len(mock_audios) + len(orphan_audios)} mock/orphan audio_abstracts records.")
        print(f"  6. Delete {len(demo_sessions)} demo chat sessions (containing {demo_messages_count} messages).")
        print(f"  7. Delete {len(empty_topics)} topics that have no remaining real paper mappings.")
        print("-" * 70)
        print("Run clean_mock_demo_data.py to clean candidates safely.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
