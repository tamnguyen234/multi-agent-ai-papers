import logging
from datetime import datetime
from app.db.database import SessionLocal
from app.services.digest_service import DigestService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

def run_daily_digest_job() -> dict:
    """
    Coordinates flow between Summarizer Agent, Database, and Email Notifications.
    Fetches the daily top 5 papers, stores them, creates a digest,
    sends daily notification emails to users, and logs the outcome.
    Returns a dictionary summarizing the job statistics.
    """
    logger.info(f"Daily digest job execution triggered at {datetime.now()}")
    db = SessionLocal()
    
    try:
        # 1. Run the daily digest database flow
        digest = DigestService.run_daily_digest_flow(db)
        
        # 2. Run the email notification flow
        results = NotificationService.send_daily_digest_notifications(db, digest)
        
        summary = {
            "digest_id": digest.id,
            "digest_date": digest.digest_date.strftime("%Y-%m-%d"),
            "total_papers": len(digest.digest_papers),
            "total_users": results["total_users"],
            "sent_count": results["sent_count"],
            "failed_count": results["failed_count"]
        }
        
        logger.info(f"Daily digest job completed. Stats: {summary}")
        return summary
        
    except Exception as e:
        error_msg = f"Daily digest job failed with exception: {str(e)}"
        logger.error(error_msg)
        return {
            "digest_id": None,
            "digest_date": datetime.now().strftime("%Y-%m-%d"),
            "total_papers": 0,
            "total_users": 0,
            "sent_count": 0,
            "failed_count": 0,
            "error": str(e)
        }
    finally:
        db.close()

def run_daily_digest():
    """Retained for backward compatibility with existing cron tasks/jobs."""
    return run_daily_digest_job()
