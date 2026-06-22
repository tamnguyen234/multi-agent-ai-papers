from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.jobs.daily_paper_job import run_daily_paper_pipeline_job
from app.core.config import settings
import logging
import pytz

logger = logging.getLogger(__name__)
scheduler = None

def start_scheduler():
    """
    Initializes and starts the BackgroundScheduler.
    Schedules the daily digest job according to configuration variables.
    Respects settings.ENABLE_SCHEDULER to allow disabling in development or reload scenarios.
    """
    global scheduler
    
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler is disabled via ENABLE_SCHEDULER configuration.")
        return
        
    if scheduler is not None:
        logger.warning("Scheduler start requested, but it is already running.")
        return
        
    try:
        # Resolve timezone
        timezone_str = settings.SCHEDULER_TIMEZONE or getattr(settings, "TIMEZONE", "Asia/Bangkok")
        tz = pytz.timezone(timezone_str)
        
        # Initialize BackgroundScheduler
        scheduler = BackgroundScheduler(timezone=tz)
        
        # Configure daily digest trigger
        trigger = CronTrigger(
            hour=settings.DAILY_DIGEST_HOUR,
            minute=settings.DAILY_DIGEST_MINUTE,
            timezone=tz
        )
        
        # Add the job
        scheduler.add_job(
            run_daily_paper_pipeline_job,
            trigger=trigger,
            id="daily_paper_pipeline_job",
            replace_existing=True
        )
        
        scheduler.start()
        msg = (
            f"Scheduler successfully started in timezone '{timezone_str}'. "
            f"Daily digest job scheduled at {settings.DAILY_DIGEST_HOUR:02d}:{settings.DAILY_DIGEST_MINUTE:02d} daily."
        )
        logger.info(msg)
        print(f"[SCHEDULER] {msg}")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        scheduler = None

def stop_scheduler():
    """
    Stops the running BackgroundScheduler gracefully.
    """
    global scheduler
    if scheduler is not None:
        try:
            scheduler.shutdown()
            logger.info("Scheduler successfully stopped.")
        except Exception as e:
            logger.error(f"Error while shutting down scheduler: {str(e)}")
        finally:
            scheduler = None
