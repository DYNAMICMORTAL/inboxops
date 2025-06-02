from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, database, main

router = APIRouter(prefix="/approvals", tags=["Approvals"])

@router.post("/", response_model=schemas.ApprovalOut)
def create_approval(
    approval: schemas.ApprovalCreate,
    db: Session = Depends(main.get_db)
):
    return crud.create_approval(db, approval)

@router.get("/", response_model=list[schemas.ApprovalOut])
def list_approvals(db: Session = Depends(main.get_db)):
    return crud.get_all_approvals(db)

@router.patch("/{approval_id}", response_model=schemas.ApprovalOut)
def update_status(
    approval_id: int,
    status: schemas.ApprovalStatus,
    db: Session = Depends(main.get_db)
):
    approval = crud.update_approval_status(db, approval_id, status)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval
