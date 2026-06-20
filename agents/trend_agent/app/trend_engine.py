import logging
from typing import List, Tuple
from app.config import settings
from app.schemas import PaperItem, TopicResponseItem
from app.rule_based_trend import analyze_rule_based
from app.bertopic_trend import analyze_bertopic

logger = logging.getLogger(__name__)

def analyze_trends_engine(papers: List[PaperItem], mode: str | None = None) -> Tuple[List[TopicResponseItem], str, str | None]:
    """
    Select and run analysis based on env and payload mode.
    Returns (topics_list, actual_mode, fallback_reason).
    """
    env_mode = settings.TREND_MODE.lower().strip()
    active_mode = mode.lower().strip() if mode else env_mode
    
    allowed_modes = ["rule_based", "real", "rule_based_fallback", "mock_fallback"]
    if active_mode not in allowed_modes:
        raise ValueError(f"Invalid mode '{active_mode}'. Allowed modes are: {', '.join(allowed_modes)}")
        
    logger.info(f"Trend Analysis starting. Mode: {active_mode}, Papers Count: {len(papers)}")
    
    if active_mode == "rule_based":
        topics = analyze_rule_based(papers)
        return topics, "rule_based", None
        
    elif active_mode == "real":
        # Force BERTopic, do not catch exceptions
        topics = analyze_bertopic(papers)
        return topics, "real", None
        
    else:  # rule_based_fallback or mock_fallback
        try:
            topics = analyze_bertopic(papers)
            return topics, "real", None
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"BERTopic clustering failed. Falling back to Rule-Based. Reason: {error_msg}")
            topics = analyze_rule_based(papers)
            return topics, active_mode, f"BERTopic failed: {error_msg}. Fell back to rule-based keyword matching."
