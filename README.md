# AI Paper Multi-Agent System

This is a comprehensive multi-agent system designed to automatically fetch, translate, analyze, and synthesize audio abstracts for the daily top trending AI papers from Hugging Face.

## Architecture & Agents

The system leverages a microservices architecture where specialized agents handle heavy processing, leaving the backend as a lightweight orchestrator and gateway.

### 1. `agents/daily_paper_audio_pipeline/`
The core orchestration workflow that runs daily at 2:00 AM.
- Fetches the top 5 trending papers from Hugging Face Daily Papers.
- **Translate Agent**: Translates the English abstract to Vietnamese.
- **TTS Agent** (located inside `daily_paper_audio_pipeline/tts_agent`): Synthesizes high-quality Vietnamese audio from the translated abstract.

### 2. `agents/trend_agent/`
A standalone AI microservice dedicated to topic modeling and clustering.
- Uses `BERTopic`, `sentence-transformers`, `UMAP`, and `HDBSCAN` to cluster paper abstracts.
- Exposes a FastAPI endpoint (`/analyze`) for the backend to request trend analysis.
- Powered by local LLMs (e.g., Llama 3.2 via Ollama) to generate human-readable topic labels.

### 3. `agents/qa_agent/`
A Retrieval-Augmented Generation (RAG) agent that allows users to chat with the PDF content of the papers.

## Getting Started

1. **Start the Agents**: Navigate to each agent directory and start their respective FastAPI servers.
2. **Start the Backend**: `cd backend && uvicorn app.main:app --reload`
3. **Start the Frontend**: `cd frontend && npm run dev`

*Ensure `.env` configuration files map the correct URLs for the agents (e.g., `TREND_AGENT_URL`, `QA_AGENT_URL`, `TTS_AGENT_URL`).*
