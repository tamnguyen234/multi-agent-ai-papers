import sys
sys.stdout.reconfigure(encoding='utf-8')

backend_path = r"c:\Users\Tung\OneDrive\Desktop\multi-agent-ai-papers-feature-agentic-integration\backend"
sys.path.append(backend_path)

from app.db.database import SessionLocal
from app.db.models.paper import Paper
from app.db.models.audio import AudioAbstract

db = SessionLocal()
try:
    papers = db.query(Paper).all()
    print(f"Total papers: {len(papers)}")
    for p in papers:
        print("="*60)
        print(f"ID: {p.id}")
        print(f"Title: {p.title[:40]}")
        print(f"has_audio: {p.has_audio}")
        print(f"abstract_vi length: {len(p.abstract_vi) if p.abstract_vi else 0}")
        if p.abstract_vi:
            print(f"abstract_vi: {p.abstract_vi[:150]}...")
        audio = db.query(AudioAbstract).filter(AudioAbstract.paper_id == p.id).first()
        if audio:
            print(f"Audio file path in DB: {audio.file_path}")
            print(f"Audio duration: {audio.duration_seconds}")
            import os
            # Check if file exists relative to project root
            proj_root = r"c:\Users\Tung\OneDrive\Desktop\multi-agent-ai-papers-feature-agentic-integration"
            full_path = os.path.join(proj_root, audio.file_path)
            print(f"Audio file exists on disk: {os.path.exists(full_path)}")
            if os.path.exists(full_path):
                print(f"Audio file size: {os.path.getsize(full_path)} bytes")
        else:
            print("No AudioAbstract record found in DB for this paper.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
