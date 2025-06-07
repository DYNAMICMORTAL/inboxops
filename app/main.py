from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from .utils import is_order_email, extract_order_details, check_email_status
from .models import Order, Approval, Email
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.utils import check_email_status
from .webhook import ai_chat
# ...existing code...

from . import models, schemas, crud
from .database import engine, SessionLocal
from .webhook import router as webhook_router
from .webhook import get_all_tickets

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="InboxOps - Inbound Email Ops Automation")

app.include_router(webhook_router)

templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["knowing-central-alpaca.ngrok-free.app", "localhost", "127.0.0.1", "inboxops.onrender.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://knowing-central-alpaca.ngrok-free.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.templating import Jinja2Templates
from app.utils import format_date
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

templates = Jinja2Templates(directory="templates")
templates.env.filters["date"] = format_date
templates.env.globals["now"] = datetime.now 

from .webhook import router as webhook_router

app.include_router(webhook_router)


from datetime import datetime

def format_received_time(received_at):
    now = datetime.now()
    if received_at.date() == now.date():
        # If the email was received today, show the time (e.g., 10:31 AM)
        return received_at.strftime("%I:%M %p")
    else:
        # If the email was received on a different day, show the month and day (e.g., Jun 2)
        return received_at.strftime("%b %d")

@app.get("/emails", response_model=List[schemas.Email])
def list_emails(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_emails(db, skip=skip, limit=limit)

@app.get("/emails/{email_id}", response_model=schemas.Email)
def get_email(email_id: int, db: Session = Depends(get_db)):
    email = crud.get_email(db, email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    emails = crud.get_emails(db, limit=20)
    return templates.TemplateResponse("home.html", {"request": request, "emails": emails, "check_email_status": check_email_status})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    print("Fetching dashboard data...")
    orders = db.query(Order).order_by(Order.id.desc()).limit(10).all()
    emails = crud.get_emails(db, limit=100)
    approvals = db.query(Approval).order_by(Approval.id.desc()).limit(10).all()
    total_processed = db.query(Email).count()
    processed_today = db.query(Email).filter(Email.received_at >= datetime.now().date()).count()
    support_tickets = get_all_tickets(db)
    processed_emails = db.query(Email).filter(Email.status == "Processed").count()
    success_rate = (processed_emails / total_processed) * 100 if total_processed else 0
    processed_yesterday = db.query(Email).filter(
        Email.received_at >= (datetime.now().date() - timedelta(days=1)),
        Email.received_at < datetime.now().date()
    ).count()
    success_rate_yesterday = (processed_yesterday / total_processed) * 100 if total_processed else 0
    success_rate_change = success_rate - success_rate_yesterday
    webhook_endpoints = 4
    avg_latency = 198
    active_models = 15
    from collections import Counter
    all_tags = [tag for order in orders if order.tags for tag in order.tags]
    if all_tags:
        tag_counts = Counter(all_tags)
        top_classification_type, top_classification_count = tag_counts.most_common(1)[0]
        top_classification_percentage = round((top_classification_count / len(all_tags)) * 100, 2)
    else:
        top_classification_type = "N/A"
        top_classification_percentage = 0
    from collections import Counter
    all_tags = [tag for order in orders if order.tags for tag in order.tags]
    if all_tags:
        tag_counts = Counter(all_tags)
        top_classification_type, top_classification_count = tag_counts.most_common(1)[0]
        top_classification_percentage = round((top_classification_count / len(all_tags)) * 100, 2)
    else:
        top_classification_type = "N/A"
        top_classification_percentage = 0
    error_rate_change = -0.8
    last_error_time = "2 hours ago"
    active_webhooks = db.query(Approval).count()
    processed_emails = db.query(Email).filter(Email.status == "Processed").count()
    success_rate = (processed_emails / total_processed) * 100 if total_processed else 0
    processed_yesterday = db.query(Email).filter(
        Email.received_at >= (datetime.now().date() - timedelta(days=1)),
        Email.received_at < datetime.now().date()
    ).count()
    success_rate_yesterday = (processed_yesterday / total_processed) * 100 if total_processed else 0
    success_rate_change = success_rate - success_rate_yesterday
    
    processing_message = "All mails processed" if success_rate == 100 else f"{success_rate:.2f}%"
    error_rate = db.query(Email).filter(Email.status == "Error").count() / total_processed * 100 if total_processed else 0

    from sqlalchemy import func
    avg_processing_time = 0
    processed_times = db.query(Email).filter(Email.status == "Processed").all()
    if processed_times:
        avg_processing_time = sum(
            [(datetime.now() - e.received_at).total_seconds() for e in processed_times]
        ) / len(processed_times)
        avg_processing_time = round(avg_processing_time / 60, 2)  # in minutes
    # Attach original mail content to each order (by matching key)
    email_map = {email.key: email for email in emails}
    # Calculate automation progress for each order
    for order in orders:
        steps = [
            bool(getattr(order, "received", False)),
            bool(getattr(order, "processed", False)),
            bool(getattr(order, "summary", False)),
        ]
        order.automation_completed = sum(steps)
        order.automation_percent = int(order.automation_completed / 3 * 100)
        order.mail_content = ""
        order.raw_json = None
        if order.key and order.key in email_map:
            email = email_map[order.key]  # <-- define email here
            order.mail_content = email_map[order.key].html_body or email_map[order.key].text_body or ""
            print(f"Order {order.id} key={order.key} mail_content={order.mail_content[:100]}")
            order.raw_json = email.raw_json  # <-- Add this

    orders_dict = [order.__dict__ for order in orders]
    emails_dict = [email.__dict__ for email in emails]

    # Debugging
    print("Total Processed:", total_processed)
    print("Processed Today:", processed_today)
    print("Success Rate:", success_rate)
    print("Error Rate:", error_rate)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "orders": orders,
            "approvals": approvals,
            "emails": emails,
            "format_date": format_date,
            "check_email_status": check_email_status,  # Pass the function to the template
            "total_processed": total_processed,
            "processed_today": processed_today,
            "processing_rate": success_rate,
            "success_rate": round(success_rate, 2),
            "success_rate_change": success_rate_change,
            "avg_processing_time": avg_processing_time,
            "active_webhooks": active_webhooks,
            "webhook_endpoints": webhook_endpoints,
            "avg_latency": avg_latency,
            "active_models": active_models,
            "top_classification_type": top_classification_type,
            "top_classification_percentage": top_classification_percentage,
            "error_rate": error_rate,
            "error_rate_change": error_rate_change,
            "last_error_time": last_error_time,
            "support_tickets": support_tickets,
        },
    )

@app.get("/orders")
def list_orders(request: Request, db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})

@app.get("/orders/{order_id}")
def order_detail(order_id: int, request: Request, db=Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    return templates.TemplateResponse("order_detail.html", {"request": request, "order": order})

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/approvals")
def list_approvals(request: Request, db=Depends(get_db)):
    approvals = db.query(Approval).all()
    return templates.TemplateResponse("approvals.html", {"request": request, "approvals": approvals})

@app.get("/approvals/{approval_id}", response_class=HTMLResponse)
def view_approval(approval_id: int, request: Request, db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    return templates.TemplateResponse("approval_detail.html", {
        "request": request,
        "approval": approval
    })

@app.post("/approvals/{approval_id}/approve")
def approve_approval(approval_id: int, db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    approval.status = "Approved"
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/approvals/{approval_id}/reject")
def reject_approval(approval_id: int, db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    approval.status = "Rejected"
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/u", response_class=HTMLResponse)
def unified_view(request: Request, page: str = "inbox", db: Session = Depends(get_db)):
    if page == "inbox":
        emails = db.query(Email).order_by(Email.received_at.desc()).all()
        format_received_time = lambda received_at: format_received_time(received_at)
        now = datetime.now()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "emails": emails, "check_email_status": check_email_status, "format_received_time": format_received_time, "now": now},
        )
    elif page == "dashboard":
        orders = db.query(Order).order_by(Order.id.desc()).all()
        approvals = db.query(Approval).order_by(Approval.id.desc()).all()
        emails = db.query(Email).order_by(Email.received_at.desc()).all()
        total_processed = db.query(Email).count()
        processed_today = db.query(Email).filter(Email.received_at >= datetime.now().date()).count()
        support_tickets = get_all_tickets(db)
        processed_emails = db.query(Email).filter(Email.status == "Processed").count()
        success_rate = (processed_emails / total_processed) * 100 if total_processed else 0
        processed_yesterday = db.query(Email).filter(
            Email.received_at >= (datetime.now().date() - timedelta(days=1)),
            Email.received_at < datetime.now().date()
        ).count()
        success_rate_yesterday = (processed_yesterday / total_processed) * 100 if total_processed else 0
        success_rate_change = success_rate - success_rate_yesterday
        active_webhooks = db.query(Approval).count() 
        webhook_endpoints = 4
        avg_latency = 198 
        active_models = 15
        # top_classification_type = "Invoices"
        # top_classification_percentage = 26.6
        from collections import Counter
        all_tags = [tag for order in orders if order.tags for tag in order.tags]
        if all_tags:
            tag_counts = Counter(all_tags)
            top_classification_type, top_classification_count = tag_counts.most_common(1)[0]
            top_classification_percentage = round((top_classification_count / len(all_tags)) * 100, 2)
        else:
            top_classification_type = "N/A"
            top_classification_percentage = 0
        error_rate = 3.2
        error_rate_change = -0.8
        last_error_time = "2 hours ago"
        emails = crud.get_emails(db, limit=1000)
        email_map = {email.key: email for email in emails}
        for order in orders:
            order.mail_content = ""
            if order.key and order.key in email_map:
                order.mail_content = email_map[order.key].html_body or email_map[order.key].text_body or ""
            print(f"Order {order.id} key={order.key} mail_content={order.mail_content[:100]}")
        from sqlalchemy import func
        avg_processing_time = 0
        processed_times = db.query(Email).filter(Email.status == "Processed").all()
        if processed_times:
            avg_processing_time = sum(
                [(datetime.now() - e.received_at).total_seconds() for e in processed_times]
            ) / len(processed_times)
            avg_processing_time = round(avg_processing_time / 60, 2)

        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "orders": orders, "emails": emails, "approvals": approvals, "check_email_status": check_email_status, "format_date": format_date, "total_processed": total_processed,
            "processed_today": processed_today,
            "processing_rate": (processed_today / total_processed) * 100 if total_processed else 0,
            "success_rate": round(success_rate, 2),
            "success_rate_change": success_rate_change,
            "avg_processing_time": avg_processing_time,
            "active_webhooks": active_webhooks,
            "webhook_endpoints": webhook_endpoints,
            "avg_latency": avg_latency,
            "active_models": active_models,
            "top_classification_type": top_classification_type,
            "top_classification_percentage": top_classification_percentage,
            "error_rate": error_rate,
            "error_rate_change": error_rate_change,
            "last_error_time": last_error_time,
            "support_tickets": support_tickets,},
        )
    else:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )

@app.get("/new", response_class=HTMLResponse)
def new_chat(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(models.SupportTicket).order_by(models.SupportTicket.created_at.desc()).limit(20).all()
    return templates.TemplateResponse("new_chat.html", {"request": request, "tickets": tickets})

@app.get("/support-customer", response_class=HTMLResponse)
def support_chat(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(models.SupportTicket).order_by(models.SupportTicket.created_at.desc()).limit(20).all()
    tickets_dict = []
    for t in tickets:
        tickets_dict.append({
            "id": t.id,
            "sender": t.sender,
            "subject": t.subject,
            "message": t.message,
            "category": t.category,
            "criticality": t.criticality,
            "status": t.status,
            "summary": t.summary,
            "tags": t.tags.split(",") if t.tags else [],
            "key": t.key,
            "assigned_to": t.assigned_to,
            "created_at": t.created_at.strftime('%b %d, %Y %H:%M') if t.created_at else "",
            "postmarkData": t.raw_json if hasattr(t, "raw_json") else {},
        })
    return templates.TemplateResponse("support_customer.html", {"request": request, "tickets": tickets_dict})