from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    digest_id = Column(BigInteger, ForeignKey("digests.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    channel = Column(Enum('email', 'in_app', name='notification_channel_enum'), default='email', nullable=False)
    status = Column(Enum('pending', 'sent', 'failed', name='notification_status_enum'), default='pending', nullable=False, index=True)
    recipient = Column(String(255), nullable=True)
    title = Column(String(500), nullable=True)
    message = Column(Text, nullable=True)  # LONGTEXT maps to Text in SQLAlchemy
    sent_at = Column(DateTime, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
    digest = relationship("Digest", back_populates="notifications")

    __table_args__ = (
        UniqueConstraint("user_id", "digest_id", "channel", name="uq_notification_user_digest_channel"),
    )
