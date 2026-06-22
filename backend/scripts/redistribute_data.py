import os
import sys
import shutil
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models.paper import Paper
from app.db.models.digest import Digest, DigestPaper

def redistribute_papers():
    db = SessionLocal()
    try:
        print("Fetching all papers...")
        papers = db.query(Paper).order_by(Paper.id).all()
        print(f"Total papers found: {len(papers)}")

        if len(papers) == 0:
            print("No papers found. Exiting.")
            return

        # 1. Clear existing digests and digest_papers to avoid conflicts
        print("Clearing existing digests and digest_papers...")
        db.query(DigestPaper).delete()
        db.query(Digest).delete()
        db.commit()

        # 2. Setup dates: Let's assume we want them ending on June 20, 2026
        # So we go backward.
        end_date = datetime(2026, 6, 20)
        
        # We will split papers into chunks of 5
        chunk_size = 5
        chunks = [papers[i:i + chunk_size] for i in range(0, len(papers), chunk_size)]
        
        print(f"Splitting into {len(chunks)} days...")

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        for idx, chunk in enumerate(reversed(chunks)):
            current_date = end_date - timedelta(days=idx)
            print(f"Processing date: {current_date.strftime('%Y-%m-%d')} with {len(chunk)} papers")

            # Create Digest
            digest = Digest(digest_date=current_date.date())
            db.add(digest)
            db.commit()
            db.refresh(digest)

            for rank, paper in enumerate(chunk, start=1):
                # Update paper dates
                paper.published = current_date.date()
                paper.created_at = current_date

                # Move PDF file if it exists
                if paper.pdf_path:
                    old_path = os.path.join(base_dir, paper.pdf_path.replace("\\", "/"))
                    if os.path.exists(old_path):
                        filename = os.path.basename(old_path)
                        new_dir_rel = f"data/paper_pdf/{current_date.strftime('%Y/%m/%d')}"
                        new_dir_abs = os.path.join(base_dir, new_dir_rel)
                        
                        os.makedirs(new_dir_abs, exist_ok=True)
                        new_path_abs = os.path.join(new_dir_abs, filename)
                        
                        # Move file
                        shutil.move(old_path, new_path_abs)
                        
                        # Update DB
                        paper.pdf_path = f"{new_dir_rel}/{filename}"

                # Create DigestPaper
                digest_paper = DigestPaper(
                    digest_id=digest.id,
                    paper_id=paper.id,
                    rank_position=rank,
                    created_at=current_date
                )
                db.add(digest_paper)

            db.commit()

        print("Redistribution complete!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    redistribute_papers()
