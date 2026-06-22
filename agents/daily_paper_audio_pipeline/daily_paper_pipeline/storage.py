from __future__ import annotations
import base64
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from daily_paper_pipeline.config import PipelineSettings, get_settings
from daily_paper_pipeline.schemas import StoredAudio, TTSResult


def _safe_extension(extension: str) -> str:
    allowed = {".wav", ".mp3", ".ogg", ".m4a"}
    if not extension.startswith("."):
        extension = f".{extension}"
    if extension.lower() not in allowed:
        raise ValueError(f"Unsupported audio extension: {extension}")
    return extension.lower()


def _static_url(relative_path: str, settings: PipelineSettings) -> str:
    prefix = settings.static_url_prefix.rstrip("/") + "/"
    return prefix + relative_path.replace("\\", "/").lstrip("/")


def save_tts_audio(
    tts_result: TTSResult,
    project_root: str | Path = ".",
    prefix: str = "abstract_tts",
    settings: PipelineSettings | None = None,
) -> StoredAudio:
    settings = settings or get_settings()
    project_root = Path(project_root).resolve()
    extension = _safe_extension(tts_result.file_extension)

    audio_bytes = base64.b64decode(tts_result.audio_base64, validate=True)
    today = datetime.now()
    base_dir = project_root / settings.audio_abstract_dir
    dated_dir = base_dir / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
    dated_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{prefix}_{uuid.uuid4().hex}{extension}"
    output_path = dated_dir / filename
    output_path.write_bytes(audio_bytes)

    relative_path = output_path.relative_to(project_root).as_posix()
    duration = int(tts_result.duration_seconds) if tts_result.duration_seconds is not None else None
    timestamps: Any = tts_result.timestamps

    return StoredAudio(
        file_path=relative_path,
        audio_url=_static_url(relative_path, settings),
        duration_seconds=duration,
        timestamps=timestamps,
    )

