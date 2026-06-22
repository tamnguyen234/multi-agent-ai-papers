from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func


Base = declarative_base()


class Paper(Base):
    __tablename__ = "papers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    external_id = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(Text, nullable=False)
    abstract_en = Column(Text, nullable=False)
    abstract_vi = Column(Text, nullable=True)
    authors = Column("authors", JSON, nullable=True)
    published = Column(Date, nullable=True, index=True)
    source_url = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    source = Column(String(100), nullable=False)
    score = Column(Float, nullable=False, default=0)
    has_audio = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    audio_abstract = relationship(
        "AudioAbstract",
        back_populates="paper",
        uselist=False,
        cascade="all, delete-orphan",
    )
    digest_papers = relationship("DigestPaper", back_populates="paper", cascade="all, delete-orphan")


class Digest(Base):
    __tablename__ = "digests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    digest_date = Column(Date, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    digest_papers = relationship("DigestPaper", back_populates="digest", cascade="all, delete-orphan")


class DigestPaper(Base):
    __tablename__ = "digest_papers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    digest_id = Column(BigInteger, ForeignKey("digests.id", ondelete="CASCADE"), nullable=False)
    paper_id = Column(BigInteger, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    rank_position = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    digest = relationship("Digest", back_populates="digest_papers")
    paper = relationship("Paper", back_populates="digest_papers")

    __table_args__ = (
        UniqueConstraint("digest_id", "paper_id", name="uq_digest_paper"),
        UniqueConstraint("digest_id", "rank_position", name="uq_digest_rank"),
        CheckConstraint("rank_position BETWEEN 1 AND 5", name="chk_rank_position"),
    )


class AudioAbstract(Base):
    __tablename__ = "audio_abstracts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    paper_id = Column(BigInteger, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    paper_timestamps = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    paper = relationship("Paper", back_populates="audio_abstract")

