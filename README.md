# AI Papers Multi-Agent System

A powerful, microservices-based Multi-Agent system for collecting, translating, analyzing, synthesizing audio, and chatting with the latest AI research papers from Hugging Face.

## 🚀 Features

- **Automated Daily Pipeline**: Fetches trending AI papers daily from Hugging Face, translates abstracts to Vietnamese using NLLB-200, and synthesizes audio summaries.
- **Microservice Architecture**: Decoupled agents (Daily Pipeline, TTS, Trend, QA) communicate via REST APIs, orchestrated by a central FastAPI backend.
- **Trend Analysis**: Automatically clusters daily papers into emerging scientific topics using SentenceTransformers and UMAP dimensionality reduction.
- **RAG Chat (QA Agent)**: Chat locally with your papers using Ollama and Llama 3 models.
- **Email Digest**: Daily automated email newsletters with the top trending papers.

## 🏗️ System Architecture

The project consists of 5 main components:

1. **Backend API Gateway (FastAPI - Port 8000)**: Orchestrates the system, serves the frontend, handles database interactions, and runs background jobs.
2. **Frontend (React + Vite - Port 5173)**: Beautiful, responsive UI to view papers, audio, trends, and chat.
3. **Daily Paper Audio Pipeline (Standalone)**: A robust pipeline job that queries Hugging Face, translates text via local NLLB-200 model, and generates TTS audio.
4. **Trend Agent (FastAPI)**: A lightweight internal service that processes text embeddings and applies UMAP to cluster papers into topics.
5. **QA Agent (Ollama)**: Local LLM integration for Retrieval-Augmented Generation.

## ⚙️ Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL Server 8.0+
- Ollama (installed locally with `llama3.2:1b` model for QA and Trend)

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tamnguyen234/multi-agent-ai-papers.git
   cd multi-agent-ai-papers
   ```

2. **Run the setup script:**
   This will install all Python and Node.js dependencies, create `.venv`s, and set up `.env` files.
   ```bash
   cd scripts
   setup_env.bat
   ```

3. **Database Setup:**
   Ensure MySQL is running, then execute the `reset_db.sql` script to create the schema.

4. **Start the System:**
   You can start all components simultaneously using the provided batch script:
   ```bash
   cd scripts
   run_all.bat
   ```

## 📜 License
MIT License
