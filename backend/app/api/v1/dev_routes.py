from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
from app.core.config import settings
from app.db.database import get_db
from app.db.models.paper import Paper
from app.db.models.digest import Digest, DigestPaper
from app.db.models.audio import AudioAbstract
from app.services import storage_service
from app.schemas.digest_schema import DigestResponse

router = APIRouter()

@router.post("/seed-sample-data", status_code=status.HTTP_201_CREATED)
def seed_sample_data(db: Session = Depends(get_db)):
    """Seed sample papers and digest for development testing. Restricted to dev environment."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seeding sample data is only permitted in development environment."
        )

    today = datetime.now().date()

    # 1. Define sample papers data
    sample_papers_data = [
        {
            "arxiv_id": "sample-001",
            "title": "Attention Is All You Need for Paper Synthesis",
            "abstract": "We present a novel multi-agent system that synthesizes academic papers. Our model uses a transformer-based coordination agent to manage search, summarization, and audio generation tasks.",
            "summary": "This paper introduces a multi-agent system for paper synthesis using transformer-based agents for task coordination.",
            "authors": ["Tâm Nguyễn", "John Doe", "Jane Smith"],
            "published": today,
            "score": 98.5,
            "has_audio": True,
            "pdf_path": "data/paper_pdf/sample-001.pdf"
        },
        {
            "arxiv_id": "sample-002",
            "title": "Generative Agents in Academic Research",
            "abstract": "This study explores the behavior of generative agents when tasked with analyzing complex AI literatures. We analyze cooperation dynamics and semantic understanding across different model scales.",
            "summary": "This study analyzes generative agents cooperating on academic literature reviews.",
            "authors": ["Tâm Nguyễn", "Alice Johnson"],
            "published": today,
            "score": 95.2,
            "has_audio": False,
            "pdf_path": "data/paper_pdf/sample-002.pdf"
        },
        {
            "arxiv_id": "sample-003",
            "title": "Large Language Models for Audio Summary Generation",
            "abstract": "We investigate methods to generate high-quality podcast-style audio summaries from academic papers. We present a text-to-speech engine optimized for technical terms.",
            "summary": "This paper presents a TTS engine optimized for technical terms to produce podcast-style audio summaries.",
            "authors": ["Bob Wilson", "Charlie Brown"],
            "published": today,
            "score": 92.0,
            "has_audio": False,
            "pdf_path": "data/paper_pdf/sample-003.pdf"
        },
        {
            "arxiv_id": "sample-004",
            "title": "Retrieval-Augmented Generation for Scientific Q&A",
            "abstract": "Retrieval-augmented generation (RAG) is a powerful approach for scientific Q&A. We evaluate different vector database structures and chunking strategies on a corpus of 10,000 AI papers.",
            "summary": "This paper evaluates vector database structures and chunking strategies for scientific Q&A.",
            "authors": ["David Miller", "Eve Watson"],
            "published": today,
            "score": 89.7,
            "has_audio": False,
            "pdf_path": "data/paper_pdf/sample-004.pdf"
        },
        {
            "arxiv_id": "sample-005",
            "title": "Analyzing AI Trends using Autonomous Web Search Agents",
            "abstract": "Autonomous web search agents can identify emerging AI topics. We propose a pipeline that continuously monitors arXiv and social media to synthesize hourly trend reports.",
            "summary": "This paper proposes a pipeline with web search agents to identify and synthesize emerging AI trends.",
            "authors": ["Tâm Nguyễn", "Frank Wright"],
            "published": today,
            "score": 87.3,
            "has_audio": False,
            "pdf_path": "data/paper_pdf/sample-005.pdf"
        },
        {
            "arxiv_id": "sample-006",
            "title": "Early Foundations of Large Language Models",
            "abstract": "A historical overview of the transition from statistical language models to deep neural network language architectures.",
            "summary": "A historical overview of early language models and deep neural architectures.",
            "authors": ["Grace Hopper"],
            "published": today - timedelta(days=10),
            "score": 80.0,
            "has_audio": False,
            "pdf_path": "data/paper_pdf/sample-006.pdf"
        },
        {
            "arxiv_id": "sample-007",
            "title": "A Survey on Multi-Agent Reinforcement Learning",
            "abstract": "We survey reinforcement learning techniques in cooperative and competitive multi-agent environments, focusing on centralized training with decentralized execution.",
            "summary": "A comprehensive survey of reinforcement learning in multi-agent environments.",
            "authors": ["Alan Turing", "John von Neumann"],
            "published": today - timedelta(days=20),
            "score": 85.0,
            "has_audio": False,
            "pdf_path": "data/paper_pdf/sample-007.pdf"
        }
    ]

    # 2. Seed papers (Insert if new, update if exists, no duplicates)
    seeded_papers = []
    for p_data in sample_papers_data:
        p = db.query(Paper).filter(Paper.arxiv_id == p_data["arxiv_id"]).first()
        if not p:
            p = Paper(
                arxiv_id=p_data["arxiv_id"],
                title=p_data["title"],
                abstract=p_data["abstract"],
                summary=p_data["summary"],
                authors=p_data["authors"],
                published=p_data["published"],
                pdf_path=p_data["pdf_path"],
                score=p_data["score"],
                has_audio=p_data["has_audio"]
            )
            db.add(p)
            db.flush()
        else:
            p.title = p_data["title"]
            p.abstract = p_data["abstract"]
            p.summary = p_data["summary"]
            p.authors = p_data["authors"]
            p.published = p_data["published"]
            p.pdf_path = p_data["pdf_path"]
            p.score = p_data["score"]
            p.has_audio = p_data["has_audio"]
            db.flush()
        seeded_papers.append(p)
    db.commit()

    # 3. Seed audio abstracts for papers that have audio
    for p in seeded_papers:
        if p.has_audio:
            audio = db.query(AudioAbstract).filter(AudioAbstract.paper_id == p.id).first()
            if not audio:
                audio = AudioAbstract(
                    paper_id=p.id,
                    file_path=f"data/audio_abstract/{p.arxiv_id}.mp3",
                    duration_seconds=120,
                    paper_timestamps={"intro": 0, "method": 30, "conclusion": 90}
                )
                db.add(audio)
            else:
                audio.file_path = f"data/audio_abstract/{p.arxiv_id}.mp3"
                audio.duration_seconds = 120
                audio.paper_timestamps = {"intro": 0, "method": 30, "conclusion": 90}
    db.commit()

    # 4. Seed today's digest (Create if new, do NOT delete/overwrite real digests)
    digest = db.query(Digest).filter(Digest.digest_date == today).first()
    if not digest:
        digest = Digest(digest_date=today)
        db.add(digest)
        db.flush()
    
    # 5. Clean up old sample mappings under today's digest and re-assign ranking
    existing_dps = db.query(DigestPaper).filter(DigestPaper.digest_id == digest.id).all()
    occupied_ranks = {}
    for dp in existing_dps:
        if not dp.paper.arxiv_id.startswith("sample-"):
            occupied_ranks[dp.rank_position] = dp.paper_id
        else:
            db.delete(dp)
    db.commit()

    # Get sample papers that should be listed in today's digest (published today)
    sample_papers_for_today = [p for p in seeded_papers if p.arxiv_id.startswith("sample-") and p.published == today]
    sample_papers_for_today = sorted(sample_papers_for_today, key=lambda x: x.score, reverse=True)

    sample_idx = 0
    for rank in range(1, 6):
        if rank in occupied_ranks:
            # Keep the real paper rank mapping
            continue
        if sample_idx < len(sample_papers_for_today):
            target_paper = sample_papers_for_today[sample_idx]
            dp = DigestPaper(
                digest_id=digest.id,
                paper_id=target_paper.id,
                rank_position=rank
            )
            db.add(dp)
            sample_idx += 1
    db.commit()

    return {"message": "Sample data seeded successfully.", "status": "ok"}

@router.post("/upload-paper-pdf")
def upload_paper_pdf(file: UploadFile = File(...)):
    """Upload paper PDF in development environment."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Storage testing is only permitted in development environment."
        )
    
    relative_path = storage_service.save_paper_pdf(file)
    url = storage_service.path_to_url(relative_path)
    return {
        "filename": Path(relative_path).name,
        "relative_path": relative_path,
        "url": url
    }

@router.post("/upload-audio-abstract")
def upload_audio_abstract(file: UploadFile = File(...)):
    """Upload audio abstract in development environment."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Storage testing is only permitted in development environment."
        )
    
    relative_path = storage_service.save_audio_abstract(file)
    url = storage_service.path_to_url(relative_path)
    return {
        "filename": Path(relative_path).name,
        "relative_path": relative_path,
        "url": url
    }

@router.post("/upload-audio-chat-message")
def upload_audio_chat_message(file: UploadFile = File(...)):
    """Upload audio chat message in development environment."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Storage testing is only permitted in development environment."
        )
    
    relative_path = storage_service.save_audio_chat_message(file)
    url = storage_service.path_to_url(relative_path)
    return {
        "filename": Path(relative_path).name,
        "relative_path": relative_path,
        "url": url
    }

@router.post("/run-summarizer-daily-top5", response_model=DigestResponse, status_code=status.HTTP_201_CREATED)
def run_summarizer_daily_top5(db: Session = Depends(get_db)):
    """Run daily top 5 summarization, update papers, and update today's digest."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual summarizer triggering is only permitted in development environment."
        )
        
    from app.services.digest_service import DigestService
    digest = DigestService.run_daily_digest_flow(db)
    
    # Sort papers of digest by rank_position ascending for response serialization
    sorted_papers = sorted(digest.digest_papers, key=lambda dp: dp.rank_position)
    return {
        "id": digest.id,
        "digest_date": digest.digest_date,
        "papers": sorted_papers
    }

from pydantic import BaseModel, EmailStr

class SendTestEmailRequest(BaseModel):
    to_email: EmailStr

@router.post("/run-daily-digest-job", status_code=status.HTTP_200_OK)
def run_daily_digest_job_endpoint():
    """Manually trigger the daily digest job (fetching, saving, emailing). Dev only."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual job triggering is only permitted in development environment."
        )
        
    from app.jobs.daily_digest_job import run_daily_digest_job
    result = run_daily_digest_job()
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job failed with error: {result['error']}"
        )
        
    return result

@router.post("/send-test-email", status_code=status.HTTP_200_OK)
def send_test_email(payload: SendTestEmailRequest):
    """Send a simple test email to verify SMTP configuration. Dev only."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sending test email is only permitted in development environment."
        )
        
    from app.services.email_service import EmailService
    
    subject = "AI Papers - SMTP Test Connection"
    html_content = """
    <html>
        <body>
            <h2 style="color: #1a0dab;">SMTP Connection Test Successful!</h2>
            <p>This is a test email sent from the AI Paper Multi-Agent System backend gateway.</p>
            <p>Time sent: {}</p>
        </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    text_content = f"SMTP Connection Test Successful!\nThis is a test email sent from the AI Paper Multi-Agent System backend gateway.\nTime sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    success = EmailService.send_email(
        to_email=payload.to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email. Please check backend log output and SMTP configuration."
        )
        
    return {"message": f"Test email sent successfully to {payload.to_email}", "status": "ok"}

@router.post("/generate-audio-abstract/{paper_id}", status_code=status.HTTP_200_OK)
def dev_generate_audio_abstract(paper_id: int, db: Session = Depends(get_db)):
    """Generate audio abstract for a specific paper. restricted to dev environment."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Generating audio abstract manually is only permitted in development environment."
        )
        
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {paper_id} not found."
        )
        
    from app.services.audio_abstract_service import generate_audio_for_paper_summary
    return generate_audio_for_paper_summary(db, paper, force=False)

@router.post("/regenerate-audio-abstract/{paper_id}", status_code=status.HTTP_200_OK)
def dev_regenerate_audio_abstract(paper_id: int, db: Session = Depends(get_db)):
    """Regenerate audio abstract for a specific paper with force=True. restricted to dev environment."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Regenerating audio abstract manually is only permitted in development environment."
        )
        
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {paper_id} not found."
        )
        
    from app.services.audio_abstract_service import generate_audio_for_paper_summary
    return generate_audio_for_paper_summary(db, paper, force=True)

@router.post("/download-paper-pdf/{paper_id}", status_code=status.HTTP_200_OK)
def dev_download_paper_pdf(paper_id: int, db: Session = Depends(get_db)):
    """Download PDF for a specific paper. Restricted to dev environment."""
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Downloading paper PDF manually is only permitted in development environment."
        )
        
    from app.services.pdf_download_service import download_and_attach_pdf
    return download_and_attach_pdf(db, paper_id)


