from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String)
    product = Column(String)
    quantity = Column(Integer)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    approval_type = Column(String)  # e.g., Leave, Budget
    request_text = Column(String)
    status = Column(String, default="Pending")  # Pending / Approved / Rejected
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)