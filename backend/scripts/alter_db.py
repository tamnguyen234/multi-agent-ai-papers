import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import engine
from sqlalchemy import text

def alter_db():
    try:
        with engine.connect() as conn:
            print("Running ALTER TABLE on papers...")
            # Ignore errors if already exists/dropped
            try:
                conn.execute(text("ALTER TABLE papers CHANGE arxiv_id external_id VARCHAR(50) NOT NULL;"))
            except Exception as e: print(e)
            
            try:
                conn.execute(text("ALTER TABLE papers CHANGE arxiv_url source_url TEXT;"))
            except Exception as e: print(e)
            
            try:
                conn.execute(text("ALTER TABLE papers CHANGE summary summary_en TEXT;"))
            except Exception as e: print(e)
            
            try:
                conn.execute(text("ALTER TABLE papers ADD COLUMN summary_vi TEXT AFTER summary_en;"))
            except Exception as e: print(e)

            try:
                conn.execute(text("ALTER TABLE papers CHANGE abstract abstract_en TEXT NOT NULL;"))
            except Exception as e: print(e)

            try:
                conn.execute(text("ALTER TABLE papers CHANGE authors_json authors JSON;"))
            except Exception as e: print(e)

            try:
                conn.execute(text("ALTER TABLE papers CHANGE trending_score score FLOAT DEFAULT 0.0;"))
            except Exception as e: print(e)

            try:
                conn.execute(text("ALTER TABLE papers ALTER COLUMN source DROP DEFAULT;"))
            except Exception as e: print(e)

            try:
                conn.execute(text("ALTER TABLE papers MODIFY COLUMN upvotes INT DEFAULT 0;"))
            except Exception as e: print(e)
            
            print("Running ALTER TABLE on chat_messages...")
            try:
                conn.execute(text("ALTER TABLE chat_messages DROP COLUMN tts_path;"))
            except Exception as e: print(e)
            
            try:
                conn.execute(text("ALTER TABLE chat_messages DROP COLUMN tts_timestamps_json;"))
            except Exception as e: print(e)

            try:
                conn.execute(text("ALTER TABLE chat_messages DROP COLUMN tts_duration_seconds;"))
            except Exception as e: print(e)
            
            print("Running ALTER TABLE on audio_abstracts...")
            try:
                conn.execute(text("ALTER TABLE audio_abstracts CHANGE paper_timestamps_json paper_timestamps JSON;"))
            except Exception as e: print(e)

            conn.commit()
            print("ALTER TABLE complete.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    alter_db()
