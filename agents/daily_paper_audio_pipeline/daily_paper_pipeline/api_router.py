from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from daily_paper_pipeline.pipeline import run_daily_summary_pipeline


def build_daily_paper_router(
    get_db_dependency: Callable,
    project_root: str | Path = ".",
) -> APIRouter:
    router = APIRouter(prefix="/daily-papers", tags=["Daily Papers"])

    @router.post("/run")
    def run_now(db: Session = Depends(get_db_dependency)):
        return run_daily_summary_pipeline(db=db, project_root=project_root)

    return router
