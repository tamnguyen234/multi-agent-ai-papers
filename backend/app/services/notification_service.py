from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.user import User
from app.db.models.notification import Notification
from app.db.models.digest import Digest
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

def build_digest_html(digest_date: str, papers: list) -> str:
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a0dab; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; }}
            .paper {{ margin-bottom: 25px; padding-bottom: 15px; border-bottom: 1px dashed #eee; }}
            .rank {{ font-size: 1.2em; font-weight: bold; color: #ff6b6b; }}
            .title {{ font-size: 1.1em; font-weight: bold; margin-left: 5px; color: #1a0dab; text-decoration: none; }}
            .meta {{ font-size: 0.9em; color: #666; margin: 5px 0; }}
            .score {{ font-weight: bold; color: #2b8a3e; }}
            .summary {{ margin-top: 10px; font-style: italic; background-color: #f9f9f9; padding: 10px; border-left: 3px solid #ccc; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI Papers Daily Digest - {digest_date}</h1>
            <p>Here are today's top 5 AI papers curated for you:</p>
    """
    for dp in papers:
        paper = dp.paper
        rank = dp.rank_position
        authors_str = ", ".join(paper.authors) if isinstance(paper.authors, list) else str(paper.authors)
        arxiv_url = f"https://arxiv.org/abs/{paper.arxiv_id}"
        
        html += f"""
            <div class="paper">
                <div>
                    <span class="rank">#{rank}</span>
                    <a class="title" href="{arxiv_url}">{paper.title}</a>
                </div>
                <div class="meta">
                    <strong>arXiv ID:</strong> {paper.arxiv_id} | 
                    <strong>Published:</strong> {paper.published} | 
                    <strong>Score:</strong> <span class="score">{paper.score}</span>
                </div>
                <div class="meta"><strong>Authors:</strong> {authors_str}</div>
                <div class="summary">
                    <strong>Summary:</strong> {paper.summary}
                </div>
            </div>
        """
    html += """
        </div>
    </body>
    </html>
    """
    return html

def build_digest_text(digest_date: str, papers: list) -> str:
    text_content = f"AI Papers Daily Digest - {digest_date}\n\n"
    text_content += "Here are today's top 5 AI papers curated for you:\n\n"
    for dp in papers:
        paper = dp.paper
        rank = dp.rank_position
        authors_str = ", ".join(paper.authors) if isinstance(paper.authors, list) else str(paper.authors)
        text_content += f"#{rank} {paper.title}\n"
        text_content += f"arXiv ID: {paper.arxiv_id} | Score: {paper.score} | Published: {paper.published}\n"
        text_content += f"Authors: {authors_str}\n"
        text_content += f"Summary: {paper.summary}\n\n"
        text_content += "-" * 40 + "\n\n"
    return text_content

class NotificationService:
    def __init__(self):
        pass

    def send_email_notification(self, recipient_email: str, subject: str, html_body: str):
        """Connect to SMTP server and send email. (Retained for compatibility)"""
        return EmailService.send_email(recipient_email, subject, html_body)

    @staticmethod
    def send_daily_digest_notifications(db: Session, digest: Digest) -> dict:
        """
        Sends daily digest emails to all users who opted-in for notifications.
        Catches individual errors so a failure for one user doesn't block the rest.
        Creates/updates notification records as required by the unique constraint.
        """
        logger.info("Starting send_daily_digest_notifications")
        
        # Get users with noti_daily enabled
        users = db.query(User).filter(User.noti_daily == True).all()
        
        digest_date_str = digest.digest_date.strftime("%Y-%m-%d")
        sorted_papers = sorted(digest.digest_papers, key=lambda dp: dp.rank_position)
        
        html_content = build_digest_html(digest_date_str, sorted_papers)
        text_content = build_digest_text(digest_date_str, sorted_papers)
        subject = f"AI Papers Daily Digest - {digest_date_str}"
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            if not user.email:
                logger.warning(f"User {user.username} has no email configured. Skipping.")
                continue
                
            logger.info(f"Sending daily digest email to user {user.username} ({user.email})")
            
            # Send the email
            success = EmailService.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            status_val = "sent" if success else "failed"
            sent_at_val = datetime.now() if success else None
            error_msg_val = None if success else "SMTP delivery failure"
            
            # Record notification status
            try:
                noti = db.query(Notification).filter(
                    Notification.user_id == user.id,
                    Notification.digest_id == digest.id,
                    Notification.channel == "email"
                ).first()
                
                if noti:
                    noti.status = status_val
                    noti.sent_at = sent_at_val
                    noti.error_message = error_msg_val
                else:
                    noti = Notification(
                        user_id=user.id,
                        digest_id=digest.id,
                        channel="email",
                        status=status_val,
                        sent_at=sent_at_val,
                        error_message=error_msg_val
                    )
                    db.add(noti)
                db.commit()
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to save notification record for user {user.username}: {str(e)}")
                db.rollback()
                failed_count += 1
                
        return {
            "total_users": len(users),
            "sent_count": sent_count,
            "failed_count": failed_count
        }
