import os
import sys
import shutil
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
from app.db.models.digest import Digest, DigestPaper
from app.db.models.audio import AudioAbstract
from app.db.models.topic import Topic, PaperTopic, TrendRun
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.notification import Notification
from app.services import storage_service

def clean_directory(dir_path: Path):
    """Delete all files and subdirectories in a directory without deleting the directory itself."""
    if not dir_path.exists():
        print(f"Thư mục không tồn tại: {dir_path}")
        return
    
    print(f"Đang dọn dẹp thư mục: {dir_path}")
    for item in dir_path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
            print(f"  Đã xóa: {item.name}")
        except Exception as e:
            print(f"  Không thể xóa {item.name}: {e}")

def main():
    db = SessionLocal()
    project_root = storage_service.get_project_root()
    
    try:
        print("=" * 60)
        print("BẮT ĐẦU XÓA TOÀN BỘ CƠ SỞ DỮ LIỆU CÁC PAPER")
        print("=" * 60)
        
        # 1. Delete database records in order
        print("\n[1/2] Đang xóa các bản ghi trong database...")
        
        print("  - Xóa DigestPaper...")
        db.query(DigestPaper).delete()
        
        print("  - Xóa PaperTopic...")
        db.query(PaperTopic).delete()
        
        print("  - Xóa AudioAbstract...")
        db.query(AudioAbstract).delete()
        
        print("  - Xóa ChatMessage...")
        db.query(ChatMessage).delete()
        
        print("  - Xóa ChatSession...")
        db.query(ChatSession).delete()
        
        print("  - Xóa Notification...")
        db.query(Notification).delete()
        
        print("  - Xóa Topic...")
        db.query(Topic).delete()
        
        print("  - Xóa TrendRun...")
        db.query(TrendRun).delete()
        
        print("  - Xóa Paper...")
        db.query(Paper).delete()
        
        print("  - Xóa Digest...")
        db.query(Digest).delete()
        
        db.commit()
        print("  => Đã xóa hoàn toàn các bản ghi trong database.")
        
        # 2. Delete physical storage assets
        print("\n[2/2] Đang xóa các tệp tin vật lý...")
        
        pdf_dir = project_root / "data" / "paper_pdf"
        audio_dir = project_root / "data" / "audio_abstract"
        faiss_dir = project_root / "data" / "faiss_indexes"
        
        clean_directory(pdf_dir)
        clean_directory(audio_dir)
        clean_directory(faiss_dir)
        
        print("\nHoàn tất dọn dẹp csdl và tệp tin thành công!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n[LỖI] Đã xảy ra lỗi trong quá trình dọn dẹp: {e}")
        print("Giao dịch database đã được rollback.")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
