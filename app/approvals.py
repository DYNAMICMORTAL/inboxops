from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, crud

router = APIRouter()

@router.post("/approvals/{approval_id}/approve")
def approve_approval(approval_id: int, db: Session = Depends(get_db)):
    approval = db.query(models.Approval).get(approval_id)
    if not approval:
        return {"error": "Approval not found"}
    approval.status = "approved"
    db.commit()
    return {"status": "approved"}

@router.post("/approvals/{approval_id}/reject")
def reject_approval(approval_id: int, db: Session = Depends(get_db)):
    approval = db.query(models.Approval).get(approval_id)
    if not approval:
        return {"error": "Approval not found"}
    approval.status = "rejected"
    db.commit()
    return {"status": "rejected"}
