from sqlalchemy.orm import Session
from . import models, schemas

def create_email(db: Session, email: schemas.EmailCreate):
    db_email = models.Email(
        from_email=email.from_email,
        subject=email.subject,
        text_body=email.text_body,
        html_body=email.html_body,
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
