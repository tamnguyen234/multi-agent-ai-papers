import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import engine
from sqlalchemy import text

def print_cols():
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SHOW COLUMNS FROM papers;"))
            for r in res:
                print(r)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print_cols()
