import os
import sys
from datetime import datetime
import json
import random

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models.paper import Paper
from app.db.models.digest import Digest, DigestPaper

def restore_from_data():
    db = SessionLocal()
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        pdf_base_dir = os.path.join(base_dir, "data", "paper_pdf")
        
        if not os.path.exists(pdf_base_dir):
            print(f"Directory {pdf_base_dir} does not exist.")
            return

        print("Clearing existing digests and papers...")
        db.query(DigestPaper).delete()
        db.query(Digest).delete()
        db.query(Paper).delete()
        db.commit()

        # Iterate over YYYY/MM/DD directories
        for year in os.listdir(pdf_base_dir):
            year_path = os.path.join(pdf_base_dir, year)
            if not os.path.isdir(year_path): continue
            
            for month in os.listdir(year_path):
                month_path = os.path.join(year_path, month)
                if not os.path.isdir(month_path): continue
                
                for day in os.listdir(month_path):
                    day_path = os.path.join(month_path, day)
                    if not os.path.isdir(day_path): continue
                    
                    # Found a day directory!
                    date_str = f"{year}-{month}-{day}"
                    try:
                        current_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        continue
                    
                    print(f"Restoring for date: {date_str}")
                    
                    # Create Digest
                    digest = Digest(digest_date=current_date.date())
                    db.add(digest)
                    db.commit()
                    db.refresh(digest)
                    
                    # Get all PDFs in this directory
                    pdfs = [f for f in os.listdir(day_path) if f.endswith(".pdf")]
                    
                    for rank, pdf_file in enumerate(pdfs, start=1):
                        # Expected format: paper_{uuid}.pdf
                        external_id = pdf_file.replace(".pdf", "")
                        
                        pdf_path_rel = f"data/paper_pdf/{year}/{month}/{day}/{pdf_file}"
                        
                        paper = Paper(
                            external_id=external_id,
                            title=f"Sample Recovered Paper {external_id[-6:]}",
                            abstract="This is a recovered abstract matching the PDF file. The original metadata was lost when the database was dropped.",
                            summary_en="This is a recovered English summary.",
                            summary_vi="Bản tóm tắt tiếng Việt khôi phục.",
                            authors=["Author A", "Author B"],
                            published=current_date.date(),
                            source_url=f"https://huggingface.co/papers/{external_id}",
                            pdf_path=pdf_path_rel,
                            source="huggingface",
                            score=random.uniform(10, 100),
                            has_audio=False,
                            created_at=current_date
                        )
                        db.add(paper)
                        db.commit()
                        db.refresh(paper)
                        
                        digest_paper = DigestPaper(
                            digest_id=digest.id,
                            paper_id=paper.id,
                            rank_position=rank,
                            created_at=current_date
                        )
                        db.add(digest_paper)
                    
                    db.commit()
                    
        print("Restore complete!")

    except Exception as e:
        print(f"Error: {repr(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore_from_data()
