from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from app.core.config import settings
from app.db.database import get_db
from app.services import storage_service

router = APIRouter()


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
        
    from app.jobs.daily_paper_job import run_daily_paper_pipeline_job
    result = run_daily_paper_pipeline_job()
    
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


