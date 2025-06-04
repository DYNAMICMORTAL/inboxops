from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas
from .webhook import is_order_email, is_approval_email
from .utils import extract_order_items, extract_tags, extract_approval_details

def create_email(db: Session, email: schemas.EmailCreate):
    date_num = datetime.now().strftime('%Y%m%d')
    # Get count of emails of each type for today
    count = db.query(models.Email).filter(
        models.Email.received_at >= datetime.now().date()
    ).count()
    
    while True:
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

        # Check if the key already exists
        existing_email = db.query(models.Email).filter(models.Email.key == key).first()
        if not existing_email:
            break
        count += 1  # Increment the counter if the key exists
    
    if is_order_email(email.subject, email.text_body):
        email_type = "ORDER"
        key = f"ODR-{date_num}{count+1:04d}"
        order_items = extract_order_items(email.text_body)
        tags = extract_tags(email.text_body)
    elif is_approval_email(email.subject, email.text_body):
        email_type = "APPROVAL"
        key = f"APL-{date_num}{count+1:04d}"
        order_items = []
        tags = []
    else:
        email_type = "SPAM"
        key = "SPAM"
        order_items = []
        tags = []

    db_email = models.Email(
        from_email=email.from_email,
        subject=email.subject,
        text_body=email.text_body,
        html_body=email.html_body,
        type=email_type,
        key=key,
        order_items=order_items,  # Save extracted order items
        tags=tags, # Save extracted tags
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


from sqlalchemy.orm import Session
from .models import Approval
from .utils import extract_approval_details

def create_approval_from_email(email, db: Session):
    """
    Create an Approval object from an email and save it to the database.
    """
    # Extract approval details from the email body
    approval_details = extract_approval_details(email.text_body)

    # Debugging
    print(f"Saving Approval: Start Date: {approval_details['start_date']}, End Date: {approval_details['end_date']}")

    new_approval = Approval(
        sender=email.from_email,
        approval_type=approval_details["approval_type"],
        request_text=approval_details["request_text"],
        start_date=approval_details["start_date"],
        end_date=approval_details["end_date"],
        created_at=email.received_at,
    )
    db.add(new_approval)
    db.commit()
    db.refresh(new_approval)
    return new_approval