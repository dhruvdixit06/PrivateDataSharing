from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/mappings", tags=["Mappings"])

# Reporting manager <-> user
@router.post("/reporting", response_model=schemas.ReportingMap)
def create_reporting_map(body: schemas.ReportingMapCreate, db: Session = Depends(get_db)):
    if db.query(models.ReportingMap).filter(
        models.ReportingMap.manager_id == body.manager_id,
        models.ReportingMap.user_id == body.user_id,
    ).first():
        raise HTTPException(400, "Mapping already exists")
    m = models.ReportingMap(manager_id=body.manager_id, user_id=body.user_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("/reporting", response_model=list[schemas.ReportingMap])
def list_reporting_maps(db: Session = Depends(get_db)):
    return db.query(models.ReportingMap).all()

# App manager map
@router.post("/app-manager", response_model=schemas.AppManagerMap)
def create_app_manager_map(body: schemas.AppManagerMapCreate, db: Session = Depends(get_db)):
    m = models.AppManagerMap(app_id=body.app_id, user_id=body.user_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("/app-manager", response_model=list[schemas.AppManagerMap])
def list_app_manager_maps(db: Session = Depends(get_db)):
    return db.query(models.AppManagerMap).all()

# App owner map
@router.post("/app-owner", response_model=schemas.AppOwnerMap)
def create_app_owner_map(body: schemas.AppOwnerMapCreate, db: Session = Depends(get_db)):
    m = models.AppOwnerMap(app_id=body.app_id, user_id=body.user_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("/app-owner", response_model=list[schemas.AppOwnerMap])
def list_app_owner_maps(db: Session = Depends(get_db)):
    return db.query(models.AppOwnerMap).all()

# Business owner map
@router.post("/business-owner", response_model=schemas.BusinessOwnerMap)
def create_bo_map(body: schemas.BusinessOwnerMapCreate, db: Session = Depends(get_db)):
    m = models.BusinessOwnerMap(app_id=body.app_id, user_id=body.user_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("/business-owner", response_model=list[schemas.BusinessOwnerMap])
def list_bo_maps(db: Session = Depends(get_db)):
    return db.query(models.BusinessOwnerMap).all()
