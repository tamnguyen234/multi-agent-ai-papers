import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the agent folder to sys.path to allow importing it
agent_path = Path("D:/multi-agent-ai/agents/daily_paper_audio_pipeline").resolve()
if str(agent_path) not in sys.path:
    sys.path.append(str(agent_path))

from app.db.database import SessionLocal
from app.db.models.digest import Digest
from app.services.storage_service import get_project_root
from app.services.notification_service import NotificationService
from app.core.config import settings

logger = logging.getLogger(__name__)

def run_daily_paper_pipeline_job() -> dict:
    """
    Job wrapper to run the external daily_paper_pipeline agent.
    This fetches 5 trending papers, translates their summaries, synthesizes audio,
    and stores them into the database.
    """
    logger.info(f"Daily paper pipeline job execution triggered at {datetime.now()}")
    db = SessionLocal()
    
    try:
        from daily_paper_pipeline.config import PipelineSettings
        from daily_paper_pipeline.pipeline import run_daily_summary_pipeline
        
        # Configure the pipeline settings with URLs from the backend's environment
        pipeline_settings = PipelineSettings(
            translate_agent_url=settings.TTS_AGENT_URL,
            tts_agent_url=settings.TTS_AGENT_URL
        )
        
        project_root = get_project_root()
        
        # Run the pipeline
        result = run_daily_summary_pipeline(
            db=db,
            project_root=project_root,
            settings=pipeline_settings
        )
        
        # Trigger Email Notifications
        digest = db.query(Digest).filter(Digest.id == result.digest_id).first()
        email_stats = None
        if digest:
            email_stats = NotificationService.send_daily_digest_notifications(db, digest)
            
        # Download PDFs for the newly processed papers
        from app.services.pdf_download_service import download_and_attach_pdf
        pdf_success_count = 0
        for paper_res in result.papers:
            try:
                logger.info(f"Attempting to download PDF for daily paper ID {paper_res.paper_id}...")
                download_and_attach_pdf(db, paper_res.paper_id)
                pdf_success_count += 1
            except Exception as e:
                logger.warning(f"Failed to download PDF for daily paper {paper_res.external_id}: {e}")
        
        summary = {
            "digest_id": result.digest_id,
            "digest_date": result.digest_date.strftime("%Y-%m-%d"),
            "total_papers": result.total_papers,
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
