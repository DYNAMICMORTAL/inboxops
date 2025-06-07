from fastapi import APIRouter, Request, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from . import crud, schemas, ai
from .ai import generate_summary  # Import the missing function
from .database import SessionLocal
from .models import Order, Approval, SupportTicket, HRRequest
from .utils import is_order_email, extract_order_details, generate_order_summary, is_approval_email, extract_approval_details, extract_order_items, extract_tags, is_support_ticket
from .support_ticket import SupportTicketCreate
import json
from postmarker.core import PostmarkClient

router = APIRouter()

# -- Postmark Config --
POSTMARK_TOKEN = "78a92885-74e3-42b0-8164-0b72fca59305"
FROM_EMAIL = "inboxops@yourdomain.com"
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
    db_email = crud.create_email(db, email_data, raw_json=json.dumps(payload))
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
        
        if is_support_ticket(email_data.subject, email_data.text_body):
            ticket_data = SupportTicketCreate(
                sender=payload.get("From"),
                subject=email_data.subject,
                message=email_data.text_body,
                key=payload.get("MessageID")
            )
        await create_ticket(db, ticket_data)



        crud.update_email_summary(db, db_email.id, "No order items found.", status="Error")
        return {"status": "⚠️ No order items found"}
    elif is_approval_email(email_data.subject, email_data.text_body):
        details = extract_approval_details(email_data.text_body)
        summary = await generate_summary(details["request_text"])
        approval = Approval(
            sender=email_data.from_email,
            approval_type=details["approval_type"],
            request_text=details["request_text"],
            status="Pending",
            start_date=details.get("start_date"),
            end_date=details.get("end_date"),
            summary=summary
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        print(f"[APPROVAL] Saved: {approval.approval_type} - {approval.status}")
        # --- NEW: Update the summary in the emails table as well ---
        crud.update_email_summary(db, db_email.id, summary, status="Processed")
        return {"status": "approval saved", "approval_type": approval.approval_type}
        

    if email_data.text_body:
        summary = await ai.generate_summary(email_data.text_body)
        crud.update_email_summary(db, db_email.id, summary)

    return {"message": "📩 Email received and processed"}


from .ai import gemini_chat
@router.post("/ai-chat")
async def ai_chat(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    user_input = data.get("message", "")

    # Fetch more context-rich data
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    approvals = db.query(Approval).order_by(Approval.created_at.desc()).limit(5).all()
    tickets = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(5).all()
    hr_requests = db.query(HRRequest).order_by(HRRequest.created_at.desc()).limit(5).all()

    # Build detailed context for each type
    order_context = "\n".join([
        f"Order ID: {o.id}, Key: {o.key}, Customer: {o.customer}, Value: {o.total_value}, Items: {o.order_items}, Tags: {o.tags}, Summary: {o.summary}"
        for o in orders
    ])
    approval_context = "\n".join([
        f"Approval ID: {a.id}, Type: {a.approval_type}, Sender: {a.sender}, Status: {a.status}, Dates: {a.start_date} to {a.end_date}, Summary: {a.summary}"
        for a in approvals
    ])
    ticket_context = "\n".join([
        f"Ticket ID: {t.id}, Issue: {t.category}, Status: {t.status}, Sender: {t.sender}, Summary: {t.summary}"
        for t in tickets
    ])
    hr_context = "\n".join([
        f"HR ID: {h.id}, Type: {h.request_type}, Sender: {h.sender}, Status: {h.status}, Summary: {h.summary}"
        for h in hr_requests
    ])

    # Optionally, include recent tags and order items
    recent_tags = []
    recent_items = []
    for o in orders:
        if o.tags:
            recent_tags.extend(o.tags)
        if o.order_items:
            recent_items.extend(o.order_items)
    tag_context = ", ".join(set(recent_tags))
    item_context = "\n".join([str(item) for item in recent_items])

    # Compose the full prompt
    context = f"""
You are an enterprise assistant for InboxOps. Here is the latest context from the system:

Recent Orders:
{order_context}

Recent Approvals:
{approval_context}

Recent Support Tickets:
{ticket_context}

Recent HR Requests:
{hr_context}

Recent Tags: {tag_context}
Recent Order Items:
{item_context}

User question: {user_input}

Answer as helpfully and accurately as possible in verbose, using the above data. Do not say you cannot access emails; you have the above data.
"""


    # answer = await generate_summary(context)
    # Build chat history for Gemini
    messages = [
        {"role": "user", "parts": [f"{context}\n\nUser question: {user_input}"]}
    ]

    answer = await gemini_chat(messages)
    return {"answer": answer}

from sqlalchemy.orm import Session
from .models import SupportTicket
from .support_ticket import SupportTicketCreate
from .utils import classify_criticality, extract_customerMail_tags, generate_summary

async def create_ticket(db: Session, ticket_data: SupportTicketCreate):
    summary = await generate_summary(ticket_data.message)
    criticality = await classify_criticality(ticket_data.message)
    tags = extract_customerMail_tags(ticket_data.message)

    db_ticket = SupportTicket(
        **ticket_data.dict(),
        summary=summary,
        criticality=criticality,
        tags=",".join(tags)
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_all_tickets(db: Session):
    return db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).all()
