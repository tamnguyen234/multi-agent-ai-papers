from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.paper import Paper
from app.db.models.digest import Digest, DigestPaper
from app.services import summarizer_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DigestService:
    def __init__(self, db: Session):
        self.db = db

    def generate_daily_digest(self):
        """Execute flow: get top 5 papers, summarize, save DB, create audio, send email notification."""
        # Kept for backward compatibility if referenced elsewhere
        return self.run_daily_digest_flow(self.db)

    def get_latest_digest(self):
        """Retrieve the most recent summary digest."""
        return self.db.query(Digest).order_by(Digest.digest_date.desc()).first()

    @staticmethod
    def run_daily_digest_flow(db: Session) -> Digest:
        """
        Coordinates the daily top 5 fetching, upserting papers,
        getting/creating digest, and safely updating rank mappings.
        """
        logger.info("Executing DigestService.run_daily_digest_flow")
        
        # 1. Fetch top 5 papers from summarizer agent client
        agent_data = summarizer_client.call_daily_top5()
        
        # Parse date from agent response
        try:
            digest_date = datetime.strptime(agent_data["date"], "%Y-%m-%d").date()
        except Exception:
            digest_date = datetime.now().date()
            
        # 2. Save or update papers in the database
        papers_to_associate = []
        new_arxiv_ids = {p_data["arxiv_id"] for p_data in agent_data["papers"]}
        
        for p_data in agent_data["papers"]:
            # Format published date string to Python date object
            try:
                date_str = p_data["published"]
                if "T" in date_str:
                    date_str = date_str.split("T")[0]
                pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            except Exception:
                pub_date = None
                
            # Auto-translate summary and abstract to Vietnamese on ingestion
            from app.services.tts_client import translate_text
            summary_vi = None
            if p_data.get("summary"):
                try:
                    summary_vi = translate_text(p_data["summary"])["translated_text"]
                except Exception as te:
                    logger.warning(f"Failed to auto-translate summary for {p_data['arxiv_id']}: {te}")
                    
            abstract_vi = None
            if p_data.get("abstract"):
                try:
                    abstract_vi = translate_text(p_data["abstract"])["translated_text"]
                except Exception as te:
                    logger.warning(f"Failed to auto-translate abstract for {p_data['arxiv_id']}: {te}")

            p = db.query(Paper).filter(Paper.arxiv_id == p_data["arxiv_id"]).first()
            if not p:
                p = Paper(
                    arxiv_id=p_data["arxiv_id"],
                    title=p_data["title"],
                    abstract=p_data["abstract"],
                    summary=p_data["summary"],
                    summary_vi=summary_vi,
                    abstract_vi=abstract_vi,
                    authors=p_data["authors"],
                    published=pub_date,
                    score=p_data["score"],
                    upvotes=p_data.get("upvotes", 0),
                    source="huggingface",
                    has_audio=False
                )
                db.add(p)
                db.flush()
            else:
                p.title = p_data["title"]
                p.abstract = p_data["abstract"]
                p.summary = p_data["summary"]
                p.summary_vi = summary_vi
                p.abstract_vi = abstract_vi
                p.authors = p_data["authors"]
                p.published = pub_date
                p.score = p_data["score"]
                p.upvotes = p_data.get("upvotes", 0)
                p.source = "huggingface"
                db.flush()
            papers_to_associate.append((p_data["rank_position"], p))
            
        # 3. Get or create digest for digest_date
        digest = db.query(Digest).filter(Digest.digest_date == digest_date).first()
        if not digest:
            digest = Digest(digest_date=digest_date)
            db.add(digest)
            db.flush()
            
        # 4. Clean up old mappings safely by deleting all old rankings for this digest
        db.query(DigestPaper).filter(DigestPaper.digest_id == digest.id).delete()
        db.commit()
        
        # 5. Insert new rankings
        papers_to_associate = sorted(papers_to_associate, key=lambda x: x[0])
        for rank, p in papers_to_associate:
            dp = DigestPaper(
                digest_id=digest.id,
                paper_id=p.id,
                rank_position=rank
            )
            db.add(dp)
            
        db.commit()
        db.refresh(digest)
        
        # 6. Generate audio abstracts for the top 5 papers
        from app.services.audio_abstract_service import generate_audio_for_paper_summary
        for dp in digest.digest_papers:
            try:
                generate_audio_for_paper_summary(db, dp.paper, force=False)
            except Exception as e:
                logger.error(
                    f"Failed to generate audio summary for paper {dp.paper.arxiv_id} (ID: {dp.paper.id}): {str(e)}"
                )
                
        # 7. Download PDF for the top 5 papers if enabled
        if settings.ENABLE_PDF_DOWNLOAD:
            from app.services.pdf_download_service import download_and_attach_pdf
            for dp in digest.digest_papers:
                try:
                    download_and_attach_pdf(db, dp.paper.id)
                except Exception as e:
                    logger.error(
                        f"Failed to download PDF for paper {dp.paper.arxiv_id} (ID: {dp.paper.id}): {str(e)}"
                    )

        return digest

