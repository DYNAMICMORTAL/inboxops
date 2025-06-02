from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from .utils import is_order_email, extract_order_details
from .models import Order

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
    return templates.TemplateResponse("index.html", {"request": request, "emails": emails})

@app.get("/orders")
def list_orders(request: Request, db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})

@app.get("/orders/{order_id}")
def order_detail(order_id: int, request: Request, db=Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    return templates.TemplateResponse("order_detail.html", {"request": request, "order": order})