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
