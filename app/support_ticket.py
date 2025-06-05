from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SupportTicketCreate(BaseModel):
    sender: str
    subject: str
    message: str
    category: Optional[str] = "General"
    criticality: Optional[str] = "Medium"
    tags: Optional[str] = None
    key: str

class SupportTicketResponse(SupportTicketCreate):
    id: int
    summary: Optional[str]
    status: str
    assigned_to: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
