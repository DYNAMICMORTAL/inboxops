from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmailBase(BaseModel):
    from_email: str
    subject: str
    text_body: Optional[str]
    html_body: Optional[str]

class EmailCreate(EmailBase):
    pass

class Email(EmailBase):
    id: int
    received_at: datetime
    summary: Optional[str]
    status: str

    class Config:
        orm_mode = True
