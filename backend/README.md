# Backend API Gateway

This is the core orchestration backend for the AI Papers Multi-Agent System. It exposes RESTful APIs, handles database interactions, and coordinates with external Microservice Agents (Translate, TTS, Trend, QA).

## Architecture

The backend is built with **FastAPI** and uses **SQLAlchemy** for database operations with **MySQL**.

### Key Responsibilities
- Serve API endpoints to the Frontend.
- Trigger and schedule the `Daily Paper Audio Pipeline` via `APScheduler`.
- Delegate translation and audio synthesis to the `TTS Agent` (via the pipeline).
- Delegate embedding and clustering calculations to the `Trend Agent`.
- Interact with local `Ollama` models for Paper QA.
- Send digest emails via SMTP.

## Directory Structure
- `app/api/v1/`: API route controllers (auth, users, papers, trends, chat, system).
- `app/core/`: Configuration, security, scheduler.
- `app/db/`: Database configuration, SQLAlchemy models, and Alembic migrations.
- `app/jobs/`: Background tasks (e.g., `daily_paper_job.py`).
- `app/schemas/`: Pydantic validation schemas.
- `app/services/`: Business logic, storage, PDF downloading, and integrations.

## Setup & Run
1. Navigate to this directory.
2. Ensure you have the `.venv` activated and requirements installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
The Swagger documentation will be available at `http://localhost:8000/docs`.
