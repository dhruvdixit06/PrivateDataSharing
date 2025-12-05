from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/access", tags=["Access"])

@router.post("/", response_model=schemas.Access)
def create_access(access: schemas.AccessCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == access.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    app = db.query(models.Application).filter(models.Application.id == access.application_id).first()
    if not app:
        raise HTTPException(404, "Application not found")
    db_access = models.Access(user_id=access.user_id, application_id=access.application_id, active=True, created_at=datetime.utcnow())
    db.add(db_access)
    db.commit()
    db.refresh(db_access)
    return db_access

@router.get("/", response_model=list[schemas.Access])
def list_access(db: Session = Depends(get_db)):
    return db.query(models.Access).all()
