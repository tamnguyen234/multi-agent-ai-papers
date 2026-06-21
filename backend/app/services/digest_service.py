from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.paper import Paper
from app.db.models.digest import Digest, DigestPaper
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
        
        # 1. Fetch top 5 papers from summarizer agent client (REMOVED)
        agent_data = {"date": datetime.now().strftime("%Y-%m-%d"), "papers": []}
        
        # Parse date from agent response
        try:
            digest_date = datetime.strptime(agent_data["date"], "%Y-%m-%d").date()
        except Exception:
            digest_date = datetime.now().date()
            
        # 2. Save or update papers in the database
        papers_to_associate = []
        new_external_ids = {p_data.get("external_id", p_data.get("arxiv_id")) for p_data in agent_data["papers"]}
        
        for p_data in agent_data["papers"]:
            # Format published date string to Python date object
            try:
                date_str = p_data["published"]
                if "T" in date_str:
                    date_str = date_str.split("T")[0]
                pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            except Exception:
                pub_date = None
                
            ext_id = p_data.get("external_id", p_data.get("arxiv_id"))
            p = db.query(Paper).filter(Paper.external_id == ext_id).first()
            if not p:
                p = Paper(
                    external_id=ext_id,
                    title=p_data["title"],
                    abstract=p_data["abstract"],
                    summary_en=p_data.get("summary_en"),
                    summary_vi=p_data.get("summary_vi", p_data.get("summary")),
                    authors=p_data["authors"],
                    published=pub_date,
                    score=p_data["score"],
                    has_audio=False,
                    source="huggingface" # Default source when fetched
                )
                db.add(p)
                db.flush()
            else:
                p.title = p_data["title"]
                p.abstract = p_data["abstract"]
                if "summary_en" in p_data:
                    p.summary_en = p_data["summary_en"]
                if "summary_vi" in p_data or "summary" in p_data:
                    p.summary_vi = p_data.get("summary_vi", p_data.get("summary"))
                p.authors = p_data["authors"]
                p.published = pub_date
                p.score = p_data["score"]
                db.flush()
            papers_to_associate.append((p_data["rank_position"], p))
            
        # 3. Get or create digest for digest_date
        digest = db.query(Digest).filter(Digest.digest_date == digest_date).first()
        if not digest:
            digest = Digest(digest_date=digest_date)
            db.add(digest)
            db.flush()
            
        # 4. Clean up old mappings safely (only mock/sample papers or those in the new result set)
        existing_dps = db.query(DigestPaper).filter(DigestPaper.digest_id == digest.id).all()
        occupied_ranks = {}
        
        for dp in existing_dps:
            ext_id = dp.paper.external_id
            is_new_result = ext_id in new_external_ids
            
            if is_new_result:
                db.delete(dp)
            else:
                occupied_ranks[dp.rank_position] = dp.paper_id
                
        db.commit()
        
        # 5. Insert new rankings
        papers_to_associate = sorted(papers_to_associate, key=lambda x: x[0])
        for rank, p in papers_to_associate:
            if rank in occupied_ranks:
                # Keep original real paper in that rank
                continue
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
                    f"Failed to generate audio summary for paper {dp.paper.external_id} (ID: {dp.paper.id}): {str(e)}"
                )
                
        # 7. Download PDF for the top 5 papers if enabled
        if settings.ENABLE_PDF_DOWNLOAD:
            from app.services.pdf_download_service import download_and_attach_pdf
            for dp in digest.digest_papers:
                try:
                    download_and_attach_pdf(db, dp.paper.id)
                except Exception as e:
                    logger.error(
                        f"Failed to download PDF for paper {dp.paper.external_id} (ID: {dp.paper.id}): {str(e)}"
                    )

        return digest

