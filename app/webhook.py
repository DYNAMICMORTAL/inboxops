from fastapi import APIRouter, Request, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from . import crud, schemas, ai
from .database import SessionLocal
from .models import Order, Approval
from .utils import is_order_email, extract_order_details, generate_order_summary, is_approval_email, extract_approval_details, extract_order_items, extract_tags
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
    print("Received email payload:", payload)

    email_data = schemas.EmailCreate(
        from_email=payload.get("From"),
        subject=payload.get("Subject", ""),
        text_body=payload.get("TextBody", ""),
        html_body=payload.get("HtmlBody", "")
    )

    # 1. Save Email Record
    db_email = crud.create_email(db, email_data)
    print("Saved email record:", db_email)

    # 2. Order Detection
    if is_order_email(email_data.subject, email_data.text_body):
        order_items = extract_order_items(email_data.text_body)
        tags = extract_tags(email_data.text_body)
        print("Extracted order items:", order_items, "tags:", tags)

        # Save order items and tags to the email record
        db_email.order_items = order_items
        db_email.tags = tags
        db.commit()
        db.refresh(db_email)

        if order_items:
            # Use the first item for summary
            summary = await generate_order_summary(order_items[0]["name"], order_items[0]["quantity"])
            print("Generated summary:", summary)

            # Save Order
            total_value = sum(item["total"] for item in order_items)
            new_order = Order(
                customer=email_data.from_email,
                product=order_items[0]["name"],
                quantity=order_items[0]["quantity"],
                order_items=order_items,
                tags=tags,
                summary=summary,
                key=db_email.key,
                total_value=total_value
            )
            db.add(new_order)
            db.commit()
            db.refresh(new_order)

            # Update Email Summary and Status
            crud.update_email_summary(db, db_email.id, summary, status="Processed")
            print("Order saved:", new_order)

            # Send Confirmation Email
            background_tasks.add_task(
                send_order_confirmation_email,
                to_email=email_data.from_email,
                order_id=new_order.id,
                summary=summary
            )

            return {"status": "✅ Order saved", "summary": summary}

        # If no items found, mark as error
        crud.update_email_summary(db, db_email.id, "No order items found.", status="Error")
        return {"status": "⚠️ No order items found"}
    elif is_approval_email(email_data.subject, email_data.text_body):
        details = extract_approval_details(email_data.text_body)
        approval = Approval(
            sender=email_data.from_email,
            approval_type=details["approval_type"],
            request_text=details["request_text"],
            status="Pending"
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        print(f"[APPROVAL] Saved: {approval.approval_type} - {approval.status}")
        return {"status": "approval saved", "approval_type": approval.approval_type}
        

    # 3. For non-order emails, generate LLM summary
    if email_data.text_body:
        summary = await ai.generate_summary(email_data.text_body)
        crud.update_email_summary(db, db_email.id, summary)

    return {"message": "📩 Email received and processed"}
