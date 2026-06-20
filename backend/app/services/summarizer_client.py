import httpx
from fastapi import HTTPException, status
from app.core.config import settings

def call_daily_top5() -> dict:
    """Call the Summarizer Agent to fetch the top 5 daily papers."""
    url = f"{settings.SUMMARIZER_AGENT_URL.rstrip('/')}/summarize/daily-top5"
    
    try:
        # Perform HTTP POST request to the summarizer agent with 120s timeout
        response = httpx.post(url, timeout=120.0)
        response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Summarizer Agent. Please ensure it is running."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to Summarizer Agent timed out after 120 seconds."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Summarizer Agent: {str(e)}"
        )
        
    data = response.json()
    
    # 1. Validation: check "papers" list exists
    if "papers" not in data or not isinstance(data["papers"], list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response format from Summarizer Agent: missing 'papers' list."
        )
        
    papers = data["papers"]
    
    # 2. Validation: check that count of papers is exactly 5
    if len(papers) != 5:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Summarizer Agent returned {len(papers)} papers. Expected exactly 5."
        )
        
    # 3. Validation: check that rank_position goes from 1 to 5
    ranks = []
    required_keys = {"rank_position", "arxiv_id", "title", "abstract", "summary", "authors", "published", "score"}
    
    for idx, paper in enumerate(papers):
        # 4. Validation: check for missing required keys
        missing_keys = required_keys - set(paper.keys())
        if missing_keys:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Paper at index {idx} is missing required fields: {', '.join(missing_keys)}."
            )
        ranks.append(paper["rank_position"])
        
    if sorted(ranks) != [1, 2, 3, 4, 5]:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invalid rank positions from Summarizer Agent: {ranks}. Must be exactly 1 to 5."
        )
            
    return data
