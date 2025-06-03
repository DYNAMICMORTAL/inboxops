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

templates = Jinja2Templates(directory="templates")
templates.env.filters["date"] = format_date

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
    orders = db.query(Order).order_by(Order.id.desc()).limit(10).all()
    emails = crud.get_emails(db, limit=20)
    approvals = db.query(Approval).order_by(Approval.id.desc()).limit(10).all()
    orders_dict = [order.__dict__ for order in orders]
    emails_dict = [email.__dict__ for email in emails]

    print("Orders:", orders_dict)
    print("Emails:", emails_dict)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "orders": orders,
            "approvals": approvals,
            "emails": emails,
            "format_date": format_date,
            "check_email_status": check_email_status,  # Pass the function to the template
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
