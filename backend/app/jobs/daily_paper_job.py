import logging
from datetime import datetime
import requests

from app.db.database import SessionLocal
from app.db.models.digest import Digest
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

DAILY_PAPER_AGENT_URL = "http://127.0.0.1:8105/api/v1/pipeline/run"

def run_daily_paper_pipeline_job() -> dict:
    """
    Job wrapper to trigger the external daily_paper_agent.
    This sends an HTTP POST request to the agent, which fetches 5 trending papers,
    translates their summaries, synthesizes audio, and stores them into the database.
    """
    logger.info(f"Daily paper pipeline job execution triggered at {datetime.now()}")
    db = SessionLocal()
    
    try:
        # Trigger the pipeline via HTTP POST
        logger.info(f"Sending request to {DAILY_PAPER_AGENT_URL}...")
        response = requests.post(
            DAILY_PAPER_AGENT_URL,
            json={"skip_audio": False},
            timeout=300 # 5 minutes timeout since TTS and translation take time
        )
        
        if response.status_code != 200:
            error_msg = f"Agent returned status {response.status_code}: {response.text}"
            logger.error(error_msg)
            return {"error": error_msg, "digest_date": datetime.now().strftime("%Y-%m-%d")}
            
        result_data = response.json()
        if result_data.get("status") != "success":
            logger.error(f"Pipeline failed: {result_data}")
            return {"error": "Pipeline failed", "details": result_data}
            
        data = result_data.get("data", {})
        digest_id = data.get("digest_id")
        digest_date = data.get("digest_date")
        total_papers = data.get("total_papers")
        papers = data.get("papers", [])
        
        # Trigger Email Notifications
        digest = db.query(Digest).filter(Digest.id == digest_id).first()
        email_stats = None
        if digest:
            email_stats = NotificationService.send_daily_digest_notifications(db, digest)
            
        # Download PDFs for the newly processed papers
        from app.services.pdf_download_service import download_and_attach_pdf
        pdf_success_count = 0
        for paper_res in papers:
            paper_id = paper_res.get("paper_id")
            if not paper_id:
                continue
            try:
                logger.info(f"Attempting to download PDF for daily paper ID {paper_id}...")
                download_and_attach_pdf(db, paper_id)
                pdf_success_count += 1
            except Exception as e:
                logger.warning(f"Failed to download PDF for daily paper {paper_id}: {e}")
        
        summary = {
            "digest_id": digest_id,
            "digest_date": digest_date,
            "total_papers": total_papers,
            "pdfs_downloaded": pdf_success_count,
            "email_stats": email_stats
        }
        
        logger.info(f"Daily paper pipeline job completed. Stats: {summary}")
        return summary
        
    except Exception as e:
        error_msg = f"Daily paper pipeline job failed with exception: {str(e)}"
        logger.error(error_msg)
        return {
            "error": str(e),
            "digest_date": datetime.now().strftime("%Y-%m-%d")
        }
    finally:
        db.close()
