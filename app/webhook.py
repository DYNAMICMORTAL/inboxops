from fastapi import APIRouter, Request, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from . import crud, schemas, ai
from .database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/inbound-email", status_code=status.HTTP_200_OK)
async def inbound_email(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    payload = await request.json()
    # Extract required fields from Postmark JSON
    email_data = schemas.EmailCreate(
        from_email=payload.get("From"),
        subject=payload.get("Subject", ""),
        text_body=payload.get("TextBody", ""),
        html_body=payload.get("HtmlBody", ""),
    )
    db_email = crud.create_email(db, email_data)

    # Call AI summary in background (async)
    if email_data.text_body:
        background_tasks.add_task(process_summary, db_email.id, email_data.text_body, db)

    return {"message": "Email received"}

async def process_summary(email_id: int, text_body: str, db: Session):
    summary = await ai.generate_summary(text_body)
    crud.update_email_summary(db, email_id, summary)