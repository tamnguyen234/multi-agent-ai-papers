import httpx
from fastapi import HTTPException, status
from app.core.config import settings

def analyze_trends(payload: dict) -> dict:
    """
    Call the Trend Agent to analyze topic distributions and keyword clusterings.
    Timeout is set to 60 seconds.
    """
    url = f"{settings.TREND_AGENT_URL.rstrip('/')}/trend/analyze"
    
    try:
        response = httpx.post(url, json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Trend Agent. Please ensure it is running."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to Trend Agent timed out after 60 seconds."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Trend Agent: {str(e)}"
        )
        
    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from Trend Agent: Response is not valid JSON."
        )
        
    # Validate required fields
    required_fields = ["mode", "total_papers", "topics"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid response format from Trend Agent: missing '{field}' field."
            )
            
    return data
