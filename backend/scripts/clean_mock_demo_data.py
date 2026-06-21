import os
import sys
import argparse
import shutil
import json
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
    parser = argparse.ArgumentParser(description="Clean mock and demo data from database and storage safely.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying database or files.")
    parser.add_argument("--apply", action="store_true", help="Apply deletions and updates to database and storage.")
    parser.add_argument("--yes-i-understand", action="store_true", help="Safety confirmation flag to proceed with cleanup.")
    parser.add_argument("--clean-orphans", action="store_true", help="Clean orphan records (non-matching relationships).")
    parser.add_argument("--clean-chat-demo", action="store_true", help="Clean demo chat sessions and messages.")
    parser.add_argument("--backup-report", action="store_true", help="Generate a backup JSON report of the cleanup.")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("ERROR: You must specify either --dry-run or --apply.")
        sys.exit(1)
        
    if args.apply and not args.yes_i_understand:
        print("ERROR: Safety flag --yes-i-understand is required with --apply to prevent accidental deletion.")
        sys.exit(1)
        
    db = SessionLocal()
    project_root = storage_service.get_project_root()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    trash_dir = project_root / "_cleanup_trash" / f"db_cleanup_{timestamp_str}"
    
    # Track statistics for reporting
    stats = {
        "deleted_papers_count": 0,
        "reassigned_digest_papers": [],
        "deleted_digest_papers_count": 0,
        "deleted_paper_topics_count": 0,
        "deleted_audio_abstracts_count": 0,
        "deleted_chat_sessions_count": 0,
        "deleted_chat_messages_count": 0,
        "deleted_notifications_count": 0,
        "deleted_topics_count": 0,
        "moved_files": []
    }
    
    try:
        # 1. Identify all mock papers and real papers
        all_papers = db.query(Paper).all()
        mock_papers = []
        real_papers = []
        for p in all_papers:
            classif = is_demo_or_mock_paper(p, project_root)
            if classif["is_mock"]:
                mock_papers.append(p)
            else:
                real_papers.append(p)
                
        mock_paper_ids = {p.id for p in mock_papers}
        real_paper_ids = {p.id for p in real_papers}
        paper_map = {p.id: p for p in all_papers}
        
        print(f"Audited papers: {len(real_papers)} Real, {len(mock_papers)} Mock/Demo.")
        
        # 2. Reassignment or deletion of DigestPaper records referencing mock papers
        # Find all digest_papers mapping to mock papers
        all_dps = db.query(DigestPaper).all()
        mock_dps = [dp for dp in all_dps if dp.paper_id in mock_paper_ids]
        orphan_dps = []
        if args.clean_orphans:
            orphan_dps = [dp for dp in all_dps if dp.paper_id not in paper_map or dp.digest_id not in {d.id for d in db.query(Digest).all()}]
            
        # For mock_dps, we want to reassign them to unassigned real papers to preserve digest counts
        in_digest_ids = {dp.paper_id for dp in all_dps if dp.paper_id in real_paper_ids}
        unassigned_real_papers = [p for p in real_papers if p.id not in in_digest_ids]
        
        reassignments = []
        dps_to_delete = []
        
        for dp in mock_dps:
            if unassigned_real_papers:
                replacement = unassigned_real_papers.pop(0)
                reassignments.append((dp, replacement))
            else:
                dps_to_delete.append(dp)
                
        dps_to_delete.extend(orphan_dps)
        
        # 3. Identify PaperTopic records to clean
        all_pts = db.query(PaperTopic).all()
        pts_to_delete = [pt for pt in all_pts if pt.paper_id in mock_paper_ids]
        if args.clean_orphans:
            all_topic_ids = {t.id for t in db.query(Topic).all()}
            pts_to_delete.extend([pt for pt in all_pts if pt.paper_id not in paper_map or pt.topic_id not in all_topic_ids])
            
        # 4. Identify AudioAbstract records to clean
        all_audios = db.query(AudioAbstract).all()
        audios_to_delete = [audio for audio in all_audios if audio.paper_id in mock_paper_ids]
        if args.clean_orphans:
            audios_to_delete.extend([audio for audio in all_audios if audio.paper_id not in paper_map])
            
        # 5. Identify ChatSessions and ChatMessages to clean
        all_sessions = db.query(ChatSession).all()
        sessions_to_delete = []
        
        for sess in all_sessions:
            is_demo = sess.paper_id in mock_paper_ids
            # If not mock by paper, check if message content contains mock keywords
            if not is_demo and args.clean_chat_demo:
                msgs = db.query(ChatMessage).filter(ChatMessage.chat_session_id == sess.id).all()
                for m in msgs:
                    content_lower = (m.content or "").lower()
                    for kw in ["mock", "demo", "test", "sample", "thử nghiệm"]:
                        if kw in content_lower:
                            is_demo = True
                            break
                    if is_demo:
                        break
            # Check orphans
            if not is_demo and args.clean_orphans:
                if sess.paper_id not in paper_map:
                    is_demo = True
            
            if is_demo:
                sessions_to_delete.append(sess)
                
        session_ids_to_delete = {sess.id for sess in sessions_to_delete}
        messages_to_delete = db.query(ChatMessage).filter(ChatMessage.chat_session_id.in_(list(session_ids_to_delete))).all()
        
        # 6. Identify Notifications to clean
        all_notifications = db.query(Notification).all()
        notifications_to_delete = []
        if args.clean_orphans:
            all_digest_ids = {d.id for d in db.query(Digest).all()}
            notifications_to_delete = [n for n in all_notifications if n.digest_id not in all_digest_ids]
            
        # 7. Collect files associated with records to delete (PDFs, Audios, Chat TTS)
        # Verify physical files exist and track their movement
        files_to_move = [] # list of (src_path_relative_or_absolute, category)
        
        # Mock paper PDFs
        for p in mock_papers:
            if p.pdf_path:
                files_to_move.append((p.pdf_path, "paper_pdf"))
                
        # Audios being deleted
        for audio in audios_to_delete:
            if audio.file_path:
                files_to_move.append((audio.file_path, "audio_abstract"))
                
        # Chat tts paths being deleted
        for msg in messages_to_delete:
            if msg.tts_path:
                files_to_move.append((msg.tts_path, "chat_tts"))
                
        # Clean relative paths and resolve duplicates
        unique_files_to_move = {}
        for path_str, cat in files_to_move:
            if not path_str or not path_str.strip():
                continue
            # Resolve to relative path under project root to prevent absolute path escapes
            clean_rel = path_str.replace("\\", "/").lstrip("/")
            full_src = project_root / clean_rel
            if full_src.is_file():
                unique_files_to_move[clean_rel] = {
                    "full_src": full_src,
                    "category": cat
                }
                
        # 8. Report or execute file movement
        print(f"Files flagged for cleanup: {len(unique_files_to_move)}")
        
        if not args.dry_run:
            # Create trash directory
            os.makedirs(trash_dir, exist_ok=True)
            for rel_path, info in unique_files_to_move.items():
                src = info["full_src"]
                dest = trash_dir / rel_path
                os.makedirs(dest.parent, exist_ok=True)
                # Move physical file
                shutil.move(str(src), str(dest))
                stats["moved_files"].append({
                    "original_path": rel_path,
                    "trash_path": str(dest.relative_to(project_root)),
                    "category": info["category"]
                })
                print(f"Moved file to trash: {rel_path} -> {dest.relative_to(project_root)}")
        else:
            for rel_path, info in unique_files_to_move.items():
                stats["moved_files"].append({
                    "original_path": rel_path,
                    "trash_path": f"_cleanup_trash/db_cleanup_DRYRUN/{rel_path}",
                    "category": info["category"]
                })
                print(f"[DRY RUN] Would move file: {rel_path}")
                
        # 9. Perform DB Updates & Deletions
        # Perform Reassignments
        for dp, replacement in reassignments:
            old_paper_id = dp.paper_id
            if not args.dry_run:
                dp.paper = replacement
            stats["reassigned_digest_papers"].append({
                "digest_id": dp.digest_id,
                "rank_position": dp.rank_position,
                "old_paper_id": old_paper_id,
                "new_paper_id": replacement.id
            })
            print(f"Reassigned DigestPaper (Digest {dp.digest_id}, Rank {dp.rank_position}): Paper ID {old_paper_id} -> {replacement.id}")
            
        # Delete DigestPapers
        stats["deleted_digest_papers_count"] = len(dps_to_delete)
        for dp in dps_to_delete:
            print(f"Deleting DigestPaper (Digest {dp.digest_id}, Paper {dp.paper_id})")
            if not args.dry_run:
                db.delete(dp)
                
        # Delete PaperTopics
        stats["deleted_paper_topics_count"] = len(pts_to_delete)
        for pt in pts_to_delete:
            print(f"Deleting PaperTopic (Paper {pt.paper_id}, Topic {pt.topic_id})")
            if not args.dry_run:
                db.delete(pt)
                
        # Delete AudioAbstracts
        stats["deleted_audio_abstracts_count"] = len(audios_to_delete)
        for audio in audios_to_delete:
            print(f"Deleting AudioAbstract ID {audio.id} for Paper {audio.paper_id}")
            if not args.dry_run:
                db.delete(audio)
                
        # Delete Notifications
        stats["deleted_notifications_count"] = len(notifications_to_delete)
        for n in notifications_to_delete:
            print(f"Deleting Notification ID {n.id}")
            if not args.dry_run:
                db.delete(n)
                
        # Delete ChatMessages
        stats["deleted_chat_messages_count"] = len(messages_to_delete)
        for msg in messages_to_delete:
            print(f"Deleting ChatMessage ID {msg.id} in Session {msg.chat_session_id}")
            if not args.dry_run:
                db.delete(msg)
                
        # Delete ChatSessions
        stats["deleted_chat_sessions_count"] = len(sessions_to_delete)
        for sess in sessions_to_delete:
            print(f"Deleting ChatSession ID {sess.id} for Paper {sess.paper_id}")
            if not args.dry_run:
                db.delete(sess)
                
        # Delete Papers
        stats["deleted_papers_count"] = len(mock_papers)
        for p in mock_papers:
            print(f"Deleting Paper ID {p.id}: {p.title[:50]}...")
            if not args.dry_run:
                db.delete(p)
                
        # Flush DB deletions/updates to evaluate topics
        if not args.dry_run:
            db.flush()
            
        # 10. Topic cleanup: Delete only topics with zero valid paper_topic mappings remaining
        all_topics = db.query(Topic).all()
        topics_to_delete = []
        for t in all_topics:
            count = db.query(PaperTopic).filter(PaperTopic.topic_id == t.id).count()
            if count == 0:
                topics_to_delete.append(t)
                
        stats["deleted_topics_count"] = len(topics_to_delete)
        for t in topics_to_delete:
            print(f"Deleting Empty Topic ID {t.id}: '{t.name}'")
            if not args.dry_run:
                db.delete(t)
                
        # Flush again before verification
        if not args.dry_run:
            db.flush()
            
        # 11. Run Verification Checks within transaction
        print("\nRunning verification checks...")
        
        if not args.dry_run:
            remaining_papers = db.query(Paper).all()
            remaining_mock_papers = []
            remaining_real_papers = []
            for p in remaining_papers:
                classif = is_demo_or_mock_paper(p, project_root)
                if classif["is_mock"]:
                    remaining_mock_papers.append(p)
                else:
                    remaining_real_papers.append(p)
            all_remaining_digests = db.query(Digest).all()
        else:
            remaining_real_papers = real_papers
            remaining_mock_papers = []
            all_remaining_digests = db.query(Digest).all()
            
        real_paper_count = len(remaining_real_papers)
        mock_paper_count = len(remaining_mock_papers)
        digest_count = len(all_remaining_digests)
        
        print(f"  * Remaining Real Papers: {real_paper_count} (Required: >= 100)")
        print(f"  * Remaining Mock Papers: {mock_paper_count} (Required: 0)")
        print(f"  * Remaining Digests: {digest_count} (Required: >= 20)")
        
        # Verify digests have exactly 5 real papers
        digest_issues = []
        remaining_real_paper_ids = {p.id for p in remaining_real_papers}
        
        for d in all_remaining_digests:
            if not args.dry_run:
                dps = db.query(DigestPaper).filter(DigestPaper.digest_id == d.id).all()
                real_p_ids_in_digest = [dp.paper_id for dp in dps if dp.paper_id in remaining_real_paper_ids]
            else:
                dps = [dp for dp in all_dps if dp.digest_id == d.id]
                real_p_ids_in_digest = []
                for dp in dps:
                    if dp in dps_to_delete:
                        continue
                    paper_id = dp.paper_id
                    for re_dp, replacement in reassignments:
                        if re_dp.id == dp.id:
                            paper_id = replacement.id
                            break
                    if paper_id in remaining_real_paper_ids:
                        real_p_ids_in_digest.append(paper_id)
                        
            if len(real_p_ids_in_digest) != 5:
                digest_issues.append(f"Digest ID {d.id} ({d.digest_date}) has {len(real_p_ids_in_digest)} real papers (expected 5)")
                
        for issue in digest_issues:
            print(f"  [Verification Issue] {issue}")
            
        # Perform assertion validations
        if mock_paper_count > 0:
            raise ValueError(f"Verification failed: Database still contains {mock_paper_count} mock/demo papers.")
            
        if real_paper_count < 100:
            raise ValueError(f"Verification failed: Real papers count {real_paper_count} is less than 100.")
            
        if digest_count < 20:
            raise ValueError(f"Verification failed: Digest count {digest_count} is less than 20.")
            
        if digest_issues:
            raise ValueError(f"Verification failed: {len(digest_issues)} digests do not have exactly 5 real papers.")
            
        print("Verification Succeeded!")
        
        # 12. Commit transaction if applying changes
        if not args.dry_run:
            db.commit()
            print("\nDatabase transaction committed successfully.")
            print(f"Successfully cleaned mock data. Physical files are backed up at:\n  {trash_dir}")
            print("You may manually delete the '_cleanup_trash' directory once satisfied.")
        else:
            db.rollback()
            print("\n[DRY RUN] Verification succeeded. Rollback performed. No database modifications made.")
            
        # 13. Backup JSON report if requested
        if args.backup_report:
            report_dir = project_root / "data" / "cleanup_reports"
            os.makedirs(report_dir, exist_ok=True)
            report_file = report_dir / f"mock_cleanup_{timestamp_str}.json"
            
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": args.dry_run,
                "statistics": {
                    "deleted_papers": stats["deleted_papers_count"],
                    "reassigned_digest_papers": len(stats["reassigned_digest_papers"]),
                    "deleted_digest_papers": stats["deleted_digest_papers_count"],
                    "deleted_paper_topics": stats["deleted_paper_topics_count"],
                    "deleted_audio_abstracts": stats["deleted_audio_abstracts_count"],
                    "deleted_chat_sessions": stats["deleted_chat_sessions_count"],
                    "deleted_chat_messages": stats["deleted_chat_messages_count"],
                    "deleted_notifications": stats["deleted_notifications_count"],
                    "deleted_topics": stats["deleted_topics_count"],
                    "moved_files_count": len(stats["moved_files"])
                },
                "reassignments": stats["reassigned_digest_papers"],
                "moved_files": stats["moved_files"]
            }
            
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"Cleanup report saved to: {report_file}")
            
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Cleanup failed: {str(e)}")
        print("Database transaction rolled back.")
        
        if not args.dry_run and stats["moved_files"]:
            print("\n" + "!" * 80)
            print("RESTORE INSTRUCTIONS:")
            print("Since physical files were moved but the database transaction was rolled back,")
            print("you must manually restore these files to synchronize storage with the database.")
            print(f"Trash Directory: {trash_dir}")
            print("\nRun the following python snippet to restore all files:")
            print(f"python -c \"")
            print("import os, shutil")
            print(f"trash_dir = r'{trash_dir}'")
            print(f"project_dir = r'{project_root}'")
            print("for root, dirs, files in os.walk(trash_dir):")
            print("    for file in files:")
            print("        src = os.path.join(root, file)")
            print("        rel = os.path.relpath(src, trash_dir)")
            print("        dest = os.path.join(project_dir, rel)")
            print("        os.makedirs(os.path.dirname(dest), exist_ok=True)")
            print("        shutil.move(src, dest)")
            print("        print(f'Restored {rel}')")
            print("\"")
            print("!" * 80 + "\n")
            
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
