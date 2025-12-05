from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.post("/", response_model=schemas.Role)
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    if db.query(models.Role).filter(models.Role.name == role.name).first():
        raise HTTPException(400, "Role already exists")
    db_role = models.Role(name=role.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/", response_model=list[schemas.Role])
def list_roles(db: Session = Depends(get_db)):
    return db.query(models.Role).all()
