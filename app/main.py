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
# ...existing code...

from . import models, schemas, crud
from .database import engine, SessionLocal
from .webhook import router as webhook_router

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
    allowed_hosts=["knowing-central-alpaca.ngrok-free.app", "localhost", "127.0.0.1"]
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
from datetime import datetime

templates = Jinja2Templates(directory="templates")
templates.env.filters["date"] = format_date
templates.env.globals["now"] = datetime.now  # Add `now` to Jinja2 globals

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
    return templates.TemplateResponse("index.html", {"request": request, "emails": emails, "check_email_status": check_email_status})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    print("Fetching dashboard data...")
    orders = db.query(Order).order_by(Order.id.desc()).limit(10).all()
    emails = crud.get_emails(db, limit=20)
    approvals = db.query(Approval).order_by(Approval.id.desc()).limit(10).all()
    total_processed = db.query(Email).count()
    processed_today = db.query(Email).filter(Email.received_at >= datetime.now().date()).count()
    success_rate = 96.8
    success_rate_change = 2.3
    avg_processing_time = 1.4  
    # active_webhooks = 12  # Example static value; replace with dynamic calculation
    webhook_endpoints = 4
    avg_latency = 198
    active_models = 15
    top_classification_type = "Invoices"
    top_classification_percentage = 26.6
    # error_rate = 3.2  # Example static value; replace with dynamic calculation
    error_rate_change = -0.8
    last_error_time = "2 hours ago"
    active_webhooks = db.query(Approval).count()
    processed_emails = db.query(Email).filter(Email.status == "Processed").count()
    processing_rate = (processed_emails / total_processed) * 100 if total_processed else 0
    processing_message = "All mails processed" if processing_rate == 100 else f"{processing_rate:.2f}%"
    error_rate = db.query(Email).filter(Email.status == "Error").count() / total_processed * 100 if total_processed else 0
    orders_dict = [order.__dict__ for order in orders]
    emails_dict = [email.__dict__ for email in emails]

    # Debugging
    print("Total Processed:", total_processed)
    print("Processed Today:", processed_today)
    print("Success Rate:", success_rate)
    print("Error Rate:", error_rate)
    # print("Orders:", orders_dict)
    # print("Emails:", emails_dict)
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
            "processing_rate": processing_rate,
            "success_rate": success_rate,
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
        success_rate = 96.8  # Example static value; replace with dynamic calculation
        success_rate_change = 2.3  # Example static value; replace with dynamic calculation
        avg_processing_time = 1.4  # Example static value; replace with dynamic calculation
        active_webhooks = 12  # Example static value; replace with dynamic calculation
        webhook_endpoints = 4  # Example static value; replace with dynamic calculation
        avg_latency = 198  # Example static value; replace with dynamic calculation
        active_models = 15  # Example static value; replace with dynamic calculation
        top_classification_type = "Invoices"  # Example static value; replace with dynamic calculation
        top_classification_percentage = 26.6  # Example static value; replace with dynamic calculation
        error_rate = 3.2  # Example static value; replace with dynamic calculation
        error_rate_change = -0.8  # Example static value; replace with dynamic calculation
        last_error_time = "2 hours ago"  # Example static value; replace with dynamic calculation
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "orders": orders, "emails": emails, "approvals": approvals, "check_email_status": check_email_status, "format_date": format_date, "total_processed": total_processed,
            "processed_today": processed_today,
            "processing_rate": (processed_today / total_processed) * 100 if total_processed else 0,
            "success_rate": success_rate,
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
            "last_error_time": last_error_time,},
        )
    else:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )