from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.business_user_id == payload.business_user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user_roles = db.query(models.Role).join(models.UserRole, models.UserRole.role_id == models.Role.id).filter(models.UserRole.user_id == user.id).all()
    return schemas.LoginResponse(user=user, roles=user_roles)
