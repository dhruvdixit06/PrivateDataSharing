from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.business_user_id == user.business_user_id).first():
        raise HTTPException(400, "business_user_id already exists")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "email already exists")
    db_user = models.User(business_user_id=user.business_user_id, name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=list[schemas.User])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
