# daily_paper_pipeline

Package copy-ready de ghep vao project multi_agent.

Package nay chi giu 4 viec can thiet:

1. Lay 5 paper trend hang ngay tu Hugging Face Daily Papers.
2. Lay summary tieng Anh co san tu Hugging Face.
3. Goi Translate Agent de dich `summary_en` sang `summary_vi`.
4. Goi TTS Agent de tao audio cho `summary_vi`, sau do luu DB.

Khong co:

- agent tu tom tat
- email notification
- PDF download
- frontend cu
- mock demo data
- trend clustering

## Cau truc

```text
daily_paper_pipeline/
  hf_daily_papers.py   # B1: fetch + rank top 5 tu Hugging Face
  agent_clients.py     # B2/B3: call /tts/translate va /tts/synthesize
  storage.py           # luu audio vao data/audio_abstract/yyyy/mm/dd
  db_models.py         # SQLAlchemy models khop DB ban gui
  pipeline.py          # orchestration B1 -> B2 -> B3 -> B4
  api_router.py        # optional FastAPI router
```

## Bien moi truong

Copy `.env.example` sang `.env` va sua URL agent neu can:

```env
HF_DAILY_PAPERS_URL=https://huggingface.co/api/daily_papers
HF_DAILY_PAPERS_POOL_LIMIT=50
TRANSLATE_AGENT_URL=http://localhost:8003
TTS_AGENT_URL=http://localhost:8003
AUDIO_ABSTRACT_DIR=data/audio_abstract
STATIC_URL_PREFIX=/static/
```

Translate/TTS agent duoc giu theo logic/model hien tai:

- Translate endpoint: `POST /tts/translate`
- TTS endpoint: `POST /tts/synthesize`

## DB mapping

Bang `papers`:

- `external_id`: HF/arXiv id
- `title`: ten paper
- `abstract`: abstract neu HF co, fallback ve `summary_en`
- `summary_en`: summary co san tu HF
- `summary_vi`: ban dich tu Translate Agent
- `authors`: JSON list
- `published`: ngay publish
- `source_url`: link HF paper
- `source`: `huggingface`
- `score`: score/rank score
- `has_audio`: true sau khi tao audio

Bang `digests`:

- `digest_date`: ngay chay pipeline

Bang `digest_papers`:

- noi digest voi 5 paper
- `rank_position`: 1..5

Bang `audio_abstracts`:

- `paper_id`
- `file_path`
- `duration_seconds`
- `paper_timestamps`

## Cach goi truc tiep trong backend

```python
from daily_paper_pipeline.pipeline import run_daily_summary_pipeline

result = run_daily_summary_pipeline(
    db=db_session,
    project_root=".",  # root project de luu data/audio_abstract
)
```

## Cach gan FastAPI router

Neu project lon cua ban da co `get_db`, co the gan router nhu sau:

```python
from daily_paper_pipeline.api_router import build_daily_paper_router
from app.db.database import get_db

app.include_router(
    build_daily_paper_router(get_db_dependency=get_db, project_root="."),
    prefix="/api/v1",
)
```

Endpoint:

```text
POST /api/v1/daily-papers/run
```

Sau khi chay xong, FE co the doc tu DB/API cua project lon:

- list 5 paper trong digest moi nhat
- hien `summary_en`
- hien `summary_vi`
- phat audio tu `audio_abstracts.file_path`

## Luu y quan trong

Package nay khong sua model dich/TTS. No chi goi agent qua HTTP.
Neu agent cua ban dang dung NLLB va VieNeu thi cu giu nguyen agent do.

