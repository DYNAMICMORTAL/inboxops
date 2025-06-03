from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr
from typing import Optional

class EmailStatus(str, Enum):
    NEW = "New"
    AWAITING = "Awaiting"
    AWAITING_APPROVAL = "Awaiting Approval"
    CLOSED = "Closed"

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
    type = Column(String, default="UNKNOWN")  # can be ORDER, APPROVAL, SPAM
    key = Column(String, unique=True)
    status = Column(String, default=EmailStatus.NEW)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String)
    product = Column(String)
    quantity = Column(Integer)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    key = Column(String, unique=True)
    total_value = Column(Float, nullable=True)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    approval_type = Column(String)  # e.g., Leave, Budget
    request_text = Column(String)
    status = Column(String, default="Pending")  # Pending / Approved / Rejected
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from datetime import datetime

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True)
    issue_type = Column(String)  # e.g., Technical, Login, Outage
    status = Column(String, default="Open")  # Open / In Progress / Resolved / Closed
    request_text = Column(Text)  # raw extracted message
    summary = Column(Text, nullable=True)  # generated from LLM
    key = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class HRRequest(Base):
    __tablename__ = "hr_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True)
    request_type = Column(String)  # Leave / Policy / Salary / Relieving Letter / etc.
    request_text = Column(Text)  # raw body
    status = Column(String, default="Pending")  # Pending / Approved / Rejected
    summary = Column(Text, nullable=True)  # generated from LLM
    key = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)