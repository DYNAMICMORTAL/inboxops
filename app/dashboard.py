from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .main import get_db
from .models import Order, Approval
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard")
def show_dashboard(request: Request, db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    approvals = db.query(Approval).all()

    tickets = [
        {
            "id": o.id,
            "type": "Order",
            "customer": o.customer,
            "title": f"{o.product} × {o.quantity}",
            "summary": o.summary,
            "status": "Approved" if o.status == "approved" else "Waiting for Support",
            "created_at": o.created_at,
        }
        for o in orders
    ] + [
        {
            "id": a.id,
            "type": "Approval",
            "customer": a.requester,
            "title": a.title,
            "summary": a.reason,
            "status": a.status.capitalize(),
            "created_at": a.created_at,
        }
        for a in approvals
    ]

    # Sort by created date, latest first
    tickets.sort(key=lambda x: x["created_at"], reverse=True)

    return templates.TemplateResponse("dashboard.html", {"request": request, "tickets": tickets})
