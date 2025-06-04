import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy.orm import Session
from app.models import Email
from app.utils import extract_order_items, extract_tags
from app.database import SessionLocal

def update_existing_emails():
    db: Session = SessionLocal()
    try:
        emails = db.query(Email).filter(Email.type == "ORDER").all()
        for email in emails:
            if email.text_body:
                # Extract order items and tags
                order_items = extract_order_items(email.text_body)
                tags = extract_tags(email.text_body)

                # Update email record
                email.order_items = order_items
                email.tags = tags
                db.commit()
                print(f"Updated email ID {email.id} with order_items and tags.")
    finally:
        db.close()

if __name__ == "__main__":
    update_existing_emails()