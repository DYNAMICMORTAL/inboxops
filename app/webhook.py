from fastapi import APIRouter, Request, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from . import crud, schemas, ai
from .database import SessionLocal
from .models import Order
from .utils import is_order_email, extract_order_details, generate_order_summary

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
        # ...existing code...
    if is_order_email(email_data.subject, email_data.text_body):
        order_data = extract_order_details(email_data.text_body)
        if order_data:
            summary = await generate_order_summary(order_data["product"], order_data["quantity"])
            db = SessionLocal()
            new_order = Order(
                customer=order_data.get("customer"),
                product=order_data.get("product"),
                quantity=order_data.get("quantity"),
                summary=summary
            )
            db.add(new_order)
            db.commit()
            db.refresh(new_order)
            # Update the summary for the email as well
            crud.update_email_summary(db, db_email.id, summary)
            db.close()
            print(f"[ORDER] Saved: {summary}")
            return {"status": "order saved", "summary": summary}
        else:
            return {"status": "unrecognized order format"}
    
    # For non-order emails, generate and save summary as before
    if email_data.text_body:
        summary = await ai.generate_summary(email_data.text_body)
        crud.update_email_summary(db, db_email.id, summary)
    
    return {"message": "Email received"}


async def process_summary(email_id: int, text_body: str, db: Session):
    summary = await ai.generate_summary(text_body)
    crud.update_email_summary(db, email_id, summary)