import re
from datetime import datetime, timezone, date, timedelta
from typing import Any

import requests

from app.config import PipelineSettings, get_settings
from app.schemas import HFDailyPaper



def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.replace("\n", " ")).strip()


def _parse_hf_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").date()
    except ValueError:
        return None


def _parse_hf_item(item: dict[str, Any]) -> HFDailyPaper | None:
    paper = item.get("paper") or {}
    external_id = paper.get("id")
    if not external_id:
        return None

    title = _clean_text(paper.get("title"))
    abstract_en = _clean_text(paper.get("abstract")) or _clean_text(paper.get("summary"))
    authors = [a.get("name", "") for a in paper.get("authors", []) if a.get("name")]
    upvotes = int(paper.get("upvotes") or item.get("upvotes") or 0)

    return HFDailyPaper(
        external_id=external_id,
        title=title,
        abstract_en=abstract_en,
        authors=authors,
        published=_parse_hf_date(paper.get("publishedAt")),
        source_url=f"https://huggingface.co/papers/{external_id}",
        upvotes=upvotes,
        score=float(upvotes),
    )


def _score_paper(paper: HFDailyPaper) -> float:
    return float(paper.upvotes)


def rank_top_papers(papers: list[HFDailyPaper], limit: int = 5) -> list[HFDailyPaper]:
    scored = []
    for paper in papers:
        scored_paper = paper.model_copy()
        scored_paper.score = _score_paper(scored_paper)
        scored.append(scored_paper)

    ranked = sorted(scored, key=lambda p: (p.score, p.external_id), reverse=True)[:limit]

    for index, paper in enumerate(ranked, start=1):
        paper.rank_position = index
    return ranked


def fetch_hf_daily_papers(
    limit: int = 5,
    settings: PipelineSettings | None = None,
    target_date: date | None = None,
) -> list[HFDailyPaper]:
    settings = settings or get_settings()
    params = {"limit": settings.hf_daily_papers_pool_limit}
    today = datetime.now().date()
    fetch_date = target_date or today
    
    if fetch_date.weekday() == 5:
        fetch_date = fetch_date - timedelta(days=1)
    elif fetch_date.weekday() == 6:
        fetch_date = fetch_date - timedelta(days=2)

    if fetch_date != today:
        params["date"] = fetch_date.strftime("%Y-%m-%d")
        
    response = requests.get(
        settings.hf_daily_papers_url,
        params=params,
        timeout=settings.http_timeout_seconds,
    )
    
    # Fallback: if HF returns 400 (e.g., date not available due to timezone), fetch latest
    if response.status_code == 400 and "date" in params:
        params.pop("date")
        response = requests.get(
            settings.hf_daily_papers_url,
            params=params,
            timeout=settings.http_timeout_seconds,
        )

    response.raise_for_status()

    seen_ids: set[str] = set()
    parsed: list[HFDailyPaper] = []
    for item in response.json():
        paper = _parse_hf_item(item)
        if not paper or paper.external_id in seen_ids:
            continue
        if not paper.title or not paper.abstract_en:
            continue
        seen_ids.add(paper.external_id)
        parsed.append(paper)

    return rank_top_papers(parsed, limit=limit)
