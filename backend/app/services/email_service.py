import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        Sends an email via SMTP.
        Returns True if successful, False if configured incorrectly or failed to send.
        Crucial: It must not crash the backend under any circumstances.
        """
        # Determine username and password
        smtp_user = settings.SMTP_USERNAME or settings.SMTP_USER
        smtp_pass = settings.SMTP_PASSWORD
        
        # Determine from address and name
        from_email = settings.SMTP_FROM_EMAIL
        from_name = settings.SMTP_FROM_NAME
        
        # Fallback parsing for old EMAIL_FROM if SMTP_FROM_EMAIL is not set
        if not from_email and settings.EMAIL_FROM:
            if "<" in settings.EMAIL_FROM and ">" in settings.EMAIL_FROM:
                from_name = settings.EMAIL_FROM.split("<")[0].strip()
                from_email = settings.EMAIL_FROM.split("<")[1].split(">")[0].strip()
            else:
                from_email = settings.EMAIL_FROM
                
        # Validate SMTP configuration
        if not settings.SMTP_HOST:
            logger.error("SMTP configuration error: SMTP_HOST is missing.")
            return False
            
        if not smtp_pass or smtp_pass == "your_gmail_app_password":
            logger.error("SMTP configuration error: SMTP_PASSWORD is not set or holds default placeholder value.")
            return False
            
        if not smtp_user or smtp_user == "your_email@gmail.com":
            logger.error("SMTP configuration error: SMTP_USERNAME/SMTP_USER is not set or holds default placeholder value.")
            return False
            
        if not from_email or from_email == "your_email@gmail.com":
            logger.error("SMTP configuration error: SMTP_FROM_EMAIL is not set or holds default placeholder value.")
            return False

        try:
            # Build email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = to_email
            
            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            if html_content:
                msg.attach(MIMEText(html_content, "html", "utf-8"))
                
            # Connect to SMTP Server with 10.0 seconds timeout
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10.0) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, to_email, msg.as_string())
                
            logger.info(f"Successfully sent email to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} due to error: {str(e)}")
            return False
