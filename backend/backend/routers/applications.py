from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/", response_model=schemas.Application)
def create_application(app: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    db_app = models.Application(name=app.name, description=app.description)
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@router.get("/", response_model=list[schemas.Application])
def list_applications(db: Session = Depends(get_db)):
    return db.query(models.Application).all()
