from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas
from .webhook import is_order_email, is_approval_email

def create_email(db: Session, email: schemas.EmailCreate):
    date_num = datetime.now().strftime('%Y%m%d')
    # Get count of emails of each type for today
    count = db.query(models.Email).filter(
        models.Email.received_at >= datetime.now().date()
    ).count()
    
    # Determine email type and generate key
    if is_order_email(email.subject, email.text_body):
        email_type = "ORDER"
        key = f"ODR-{date_num}{count+1:04d}"
    elif is_approval_email(email.subject, email.text_body):
        email_type = "APPROVAL"
        key = f"APL-{date_num}{count+1:04d}"
    else:
        email_type = "SPAM"
        key = "SPAM"
    db_email = models.Email(
        from_email=email.from_email,
        subject=email.subject,
        text_body=email.text_body,
        html_body=email.html_body,
        type=email_type,
        key=key
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

def get_emails(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Email).offset(skip).limit(limit).all()

def get_email(db: Session, email_id: int):
    return db.query(models.Email).filter(models.Email.id == email_id).first()

def update_email_summary(db: Session, email_id: int, summary: str, status: str = "processed"):
    email = get_email(db, email_id)
    if email:
        email.summary = summary
        email.status = status
        db.commit()
        db.refresh(email)
    return email
