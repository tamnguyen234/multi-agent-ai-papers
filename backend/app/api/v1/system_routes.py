from fastapi import APIRouter, status, Response
from app.db.database import check_database_connection
from app.schemas.system_schema import DBHealthResponse

router = APIRouter()

@router.get("/db-health", response_model=DBHealthResponse)
def get_db_health(response: Response):
    """Check MySQL database connection status."""
    is_connected = check_database_connection()
    if is_connected:
        return DBHealthResponse(
            status="ok",
            database="connected"
        )
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DBHealthResponse(
            status="error",
            database="disconnected",
            detail="Unable to establish a connection to the MySQL database. Please verify configuration settings and state."
        )

@router.get("/scheduler-status")
def get_scheduler_status():
    """Get status of the daily scheduler and its scheduled jobs."""
    from app.core.scheduler import scheduler
    if scheduler is None:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
            "pending": job.pending
        })
    return {
        "running": scheduler.running,
        "jobs": jobs
    }

