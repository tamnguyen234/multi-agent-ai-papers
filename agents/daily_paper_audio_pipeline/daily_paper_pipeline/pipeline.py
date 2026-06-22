from datetime import date, datetime
from pathlib import Path

from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

from daily_paper_pipeline.agent_clients import TTSClient
from daily_paper_pipeline.config import PipelineSettings, get_settings
from daily_paper_pipeline.db_models import AudioAbstract, Digest, DigestPaper, Paper
from daily_paper_pipeline.hf_daily_papers import fetch_hf_daily_papers
from daily_paper_pipeline.schemas import DailyPipelineResult, HFDailyPaper, PipelinePaperResult
from daily_paper_pipeline.storage import save_tts_audio


def _get_or_create_digest(db: Session, digest_date: date) -> Digest:
    digest = db.query(Digest).filter(Digest.digest_date == digest_date).first()
    if digest:
        return digest
    digest = Digest(digest_date=digest_date)
    db.add(digest)
    db.flush()
    return digest


def _upsert_paper(db: Session, hf_paper: HFDailyPaper, summary_vi: str | None) -> Paper:
    paper = db.query(Paper).filter(Paper.external_id == hf_paper.external_id).first()
    data = {
        "title": hf_paper.title,
        "abstract_en": hf_paper.abstract_en,
        "abstract_vi": summary_vi,
        "authors": hf_paper.authors,
        "published": hf_paper.published,
        "source_url": hf_paper.source_url,
        "source": "huggingface",
        "score": hf_paper.score,
    }

    if paper is None:
        paper = Paper(external_id=hf_paper.external_id, has_audio=False, **data)
        db.add(paper)
    else:
        for key, value in data.items():
            setattr(paper, key, value)
    db.flush()
    return paper


def _replace_digest_ranks(db: Session, digest: Digest, ranked_papers: list[tuple[int, Paper]]) -> None:
    db.query(DigestPaper).filter(DigestPaper.digest_id == digest.id).delete()
    db.flush()
    for rank_position, paper in ranked_papers:
        db.add(DigestPaper(digest_id=digest.id, paper_id=paper.id, rank_position=rank_position))
    db.flush()


def _upsert_audio_abstract(db: Session, paper: Paper, stored_audio) -> AudioAbstract:
    audio = db.query(AudioAbstract).filter(AudioAbstract.paper_id == paper.id).first()
    if audio is None:
        audio = AudioAbstract(paper_id=paper.id, file_path=stored_audio.file_path)
        db.add(audio)

    audio.file_path = stored_audio.file_path
    audio.duration_seconds = stored_audio.duration_seconds
    audio.paper_timestamps = stored_audio.timestamps
    paper.has_audio = True
    db.flush()
    return audio


def run_daily_summary_pipeline(
    db: Session,
    digest_date: date | None = None,
    project_root: str | Path = ".",
    settings: PipelineSettings | None = None,
    skip_audio: bool = False,
) -> DailyPipelineResult:
    settings = settings or get_settings()
    digest_date = digest_date or datetime.now().date()

    tts_client = TTSClient(settings)

    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading NLLB model on {device}...")
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M").to(device)
    logger.info("NLLB model loaded.")

    hf_papers = fetch_hf_daily_papers(limit=5, settings=settings, target_date=digest_date)
    if not hf_papers:
        logger.warning(f"No Hugging Face daily papers found for {digest_date}.")
        return DailyPipelineResult(
            digest_id=0,
            digest_date=digest_date,
            total_papers=0,
            papers=[],
        )
    if len(hf_papers) < 5:
        logger.warning(f"Expected 5 Hugging Face daily papers, got {len(hf_papers)}.")

    digest = _get_or_create_digest(db, digest_date)
    ranked_db_papers: list[tuple[int, Paper]] = []
    result_items: list[PipelinePaperResult] = []

    try:
        for hf_paper in hf_papers:
            rank_position = hf_paper.rank_position or len(ranked_db_papers) + 1
            logger.info("Translating abstract_en...")
            try:
                inputs = tokenizer(hf_paper.abstract_en, return_tensors="pt").to(device)
                translated_tokens = model.generate(
                    **inputs, forced_bos_token_id=tokenizer.convert_tokens_to_ids("vie_Latn"), max_length=1024
                )
                summary_vi_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
                logger.info("Translation complete.")
            except Exception as e:
                logger.warning(f"Translation failed, using fallback: {e}")
                summary_vi_text = f"[Bản dịch giả lập] {hf_paper.abstract_en}"
            paper = _upsert_paper(db, hf_paper, summary_vi_text)
            ranked_db_papers.append((rank_position, paper))

        _replace_digest_ranks(db, digest, ranked_db_papers)
        db.commit()
    except Exception:
        db.rollback()
        raise

    for rank_position, paper in ranked_db_papers:
        audio_path = None
        audio_url = None
        if not skip_audio:
            try:
                if not paper.abstract_vi or not paper.abstract_vi.strip():
                    raise ValueError(f"Paper {paper.external_id} has empty Vietnamese abstract.")
                
                tts_text = paper.abstract_vi.strip()
                if len(tts_text) > 1950:
                    logger.info(f"Truncating abstract_vi for TTS from {len(tts_text)} to 1950 chars.")
                    tts_text = tts_text[:1950] + "..."
                    
                tts_result = tts_client.synthesize_vi(tts_text)
                stored_audio = save_tts_audio(tts_result, project_root=project_root, settings=settings)
                _upsert_audio_abstract(db, paper, stored_audio)
                db.commit()
                audio_path = stored_audio.file_path
                audio_url = stored_audio.audio_url
            except Exception:
                db.rollback()
                raise

        result_items.append(
            PipelinePaperResult(
                paper_id=int(paper.id),
                external_id=paper.external_id,
                rank_position=rank_position,
                title=paper.title,
                abstract_en=paper.abstract_en or "",
                abstract_vi=paper.abstract_vi,
                audio_path=audio_path,
                audio_url=audio_url,
            )
        )

    return DailyPipelineResult(
        digest_id=int(digest.id),
        digest_date=digest.digest_date,
        total_papers=len(result_items),
        papers=result_items,
    )

