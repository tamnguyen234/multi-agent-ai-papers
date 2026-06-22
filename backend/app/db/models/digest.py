from sqlalchemy import Column, BigInteger, Integer, Date, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Digest(Base):
    __tablename__ = "digests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    digest_date = Column(Date, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    digest_papers = relationship("DigestPaper", back_populates="digest", cascade="all, delete-orphan")

class DigestPaper(Base):
    __tablename__ = "digest_papers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    digest_id = Column(BigInteger, ForeignKey("digests.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    paper_id = Column(BigInteger, ForeignKey("papers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    rank_position = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


    # Relationships
    digest = relationship("Digest", back_populates="digest_papers")
    paper = relationship("Paper", back_populates="digest_papers")

    # Constraints
    __table_args__ = (
        UniqueConstraint("digest_id", "paper_id", name="uq_digest_paper"),
        UniqueConstraint("digest_id", "rank_position", name="uq_digest_rank"),
        CheckConstraint("rank_position BETWEEN 1 AND 5", name="chk_rank_position"),
    )
