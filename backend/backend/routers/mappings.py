from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models

router = APIRouter(prefix="/mappings", tags=["Mappings"])

@router.post("/reporting-app")
def create_reporting_app_map(body: dict, db: Session = Depends(get_db)):
    manager_id = body.get("manager_id")
    app_id = body.get("app_id")
    if not manager_id or not app_id:
        raise HTTPException(400, "manager_id and app_id required")
    if db.query(models.ReportingAppMap).filter(models.ReportingAppMap.manager_id == manager_id, models.ReportingAppMap.app_id == app_id).first():
        raise HTTPException(400, "Mapping exists")
    m = models.ReportingAppMap(manager_id=manager_id, app_id=app_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "manager_id": m.manager_id, "app_id": m.app_id}

@router.get("/reporting-app")
def list_reporting_app_maps(db: Session = Depends(get_db)):
    return db.query(models.ReportingAppMap).all()
