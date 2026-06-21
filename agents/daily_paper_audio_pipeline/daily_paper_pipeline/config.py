from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hf_daily_papers_url: str = "https://huggingface.co/api/daily_papers"
    hf_daily_papers_pool_limit: int = 50

    translate_agent_url: str = "http://localhost:8003"
    tts_agent_url: str = "http://localhost:8003"

    audio_abstract_dir: str = "data/audio_abstract"
    static_url_prefix: str = "/static/"

    http_timeout_seconds: float = Field(default=120.0, ge=1.0)
    tts_timeout_seconds: float = Field(default=300.0, ge=1.0)


@lru_cache(maxsize=1)
def get_settings() -> PipelineSettings:
    return PipelineSettings()

