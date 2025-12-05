from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/user-roles", tags=["User Roles"])

@router.post("/assign", response_model=schemas.UserRole)
def assign_role(ur: schemas.UserRoleCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == ur.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    role = db.query(models.Role).filter(models.Role.id == ur.role_id).first()
    if not role:
        raise HTTPException(404, "Role not found")
    existing = db.query(models.UserRole).filter(models.UserRole.user_id == ur.user_id, models.UserRole.role_id == ur.role_id).first()
    if existing:
        raise HTTPException(400, "User already has this role")
    db_ur = models.UserRole(user_id=ur.user_id, role_id=ur.role_id)
    db.add(db_ur)
    db.commit()
    db.refresh(db_ur)
    return db_ur

@router.get("/by-user/{user_id}", response_model=list[schemas.UserRole])
def list_roles_for_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.UserRole).filter(models.UserRole.user_id == user_id).all()
