from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    from_email = Column(String, index=True)
    subject = Column(String, index=True)
    text_body = Column(Text)
    html_body = Column(Text)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    summary = Column(Text, nullable=True)
    status = Column(String, default="received")
