import httpx
from fastapi import HTTPException, status
from app.core.config import settings

def ask_question(payload: dict) -> dict:
    """
    Call the Q&A Agent to ask a question about a paper.
    Timeout follows the Agent2-style Ollama chat timeout budget.
    """
    url = f"{settings.QA_AGENT_URL.rstrip('/')}/qa/ask"
    
    try:
        response = httpx.post(url, json=payload, timeout=620.0)
        response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Q&A Agent. Please ensure it is running."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to Q&A Agent timed out after 620 seconds."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Q&A Agent: {str(e)}"
        )
        
    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from Q&A Agent: Response is not valid JSON."
        )
        
    if "answer" not in data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response format from Q&A Agent: missing 'answer' field."
        )
        
    # Ensure mode and sources exist in response
    return {
        "answer": data["answer"],
        "mode": data.get("mode", "real"),
        "sources": data.get("sources", [])
    }
