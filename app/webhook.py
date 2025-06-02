from fastapi import APIRouter, Request, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from . import crud, schemas, ai
from .database import SessionLocal
from .models import Order
from .utils import is_order_email, extract_order_details, generate_order_summary
from postmarker.core import PostmarkClient

router = APIRouter()

# -- Postmark Config --
POSTMARK_TOKEN = "78a92885-74e3-42b0-8164-0b72fca59305"
FROM_EMAIL = "inboxops@yourdomain.com"  # Set this to your sender domain
postmark = PostmarkClient(server_token=POSTMARK_TOKEN)

# -- Get DB --
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -- Confirmation Email Sender --
def send_order_confirmation_email(to_email: str, order_id: int, summary: str):
    try:
        postmark.emails.send(
            From=FROM_EMAIL,
            To=to_email,
            Subject=f"✅ Order {order_id} Confirmed!",
            HtmlBody=f"""
                <h2>Thank you for your order!</h2>
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Summary:</strong><br>{summary}</p>
                <br><p>— InboxOps</p>
            """,
            TextBody=f"""Order ID: {order_id}\nSummary: {summary}\n— InboxOps"""
        )
        print(f"✅ Confirmation email sent to {to_email}")
    except Exception as e:
        print("❌ Email sending failed:", str(e))


@router.post("/inbound-email", status_code=status.HTTP_200_OK)
async def inbound_email(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    payload = await request.json()

    email_data = schemas.EmailCreate(
        from_email=payload.get("From"),
        subject=payload.get("Subject", ""),
        text_body=payload.get("TextBody", ""),
        html_body=payload.get("HtmlBody", "")
    )

    # 1. Save Email Record
    db_email = crud.create_email(db, email_data)

    # 2. Order Detection
    if is_order_email(email_data.subject, email_data.text_body):
        order_data = extract_order_details(email_data.text_body)
        if order_data:
            summary = await generate_order_summary(order_data["product"], order_data["quantity"])

            # 3. Save Order
            new_order = Order(
                customer=order_data.get("customer"),
                product=order_data.get("product"),
                quantity=order_data.get("quantity"),
                summary=summary
            )
            db.add(new_order)
            db.commit()
            db.refresh(new_order)

            # 4. Update Email Summary
            crud.update_email_summary(db, db_email.id, summary)

            # 5. Send Confirmation Email in Background
            background_tasks.add_task(
                send_order_confirmation_email,
                to_email=email_data.from_email,
                order_id=new_order.id,
                summary=summary
            )

            return {"status": "✅ Order saved", "summary": summary}

        return {"status": "⚠️ Unrecognized order format"}

    # 3. For non-order emails, generate LLM summary
    if email_data.text_body:
        summary = await ai.generate_summary(email_data.text_body)
        crud.update_email_summary(db, db_email.id, summary)

    return {"message": "📩 Email received and processed"}
