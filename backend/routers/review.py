from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from backend.db.database import get_db
from backend.db import models, schemas

router = APIRouter(prefix="/review", tags=["Review & Workflow"])

@router.post("/start-cycle")
def start_cycle(quarter: str, db: Session = Depends(get_db)):
    cycle = models.ReviewCycle(quarter=quarter, status="in_progress")
    db.add(cycle)
    db.commit()
    db.refresh(cycle)

    accesses = db.query(models.Access).filter(models.Access.active == True).all()

    for acc in accesses:
        # find reporting manager for this user
        rm_map = db.query(models.ReportingMap).filter(models.ReportingMap.user_id == acc.user_id).first()
        reporting_manager_id = rm_map.manager_id if rm_map else None

        # app manager
        am_map = db.query(models.AppManagerMap).filter(models.AppManagerMap.app_id == acc.application_id).first()
        app_manager_id = am_map.user_id if am_map else None

        # app owner
        ao_map = db.query(models.AppOwnerMap).filter(models.AppOwnerMap.app_id == acc.application_id).first()
        app_owner_id = ao_map.user_id if ao_map else None

        # business owner
        bo_map = db.query(models.BusinessOwnerMap).filter(models.BusinessOwnerMap.app_id == acc.application_id).first()
        business_owner_id = bo_map.user_id if bo_map else None

        if reporting_manager_id:
            pending_stage = "reporting_manager"
        elif app_manager_id:
            pending_stage = "app_manager"
        elif app_owner_id:
            pending_stage = "app_owner"
        elif business_owner_id:
            pending_stage = "business_owner"
        else:
            pending_stage = "completed"

        item = models.ReviewItem(
            cycle_id=cycle.id,
            access_id=acc.id,
            reporting_manager_id=reporting_manager_id,
            app_manager_id=app_manager_id,
            app_owner_id=app_owner_id,
            business_owner_id=business_owner_id,
            pending_stage=pending_stage,
        )
        db.add(item)

    db.commit()
    return {"message": "Review cycle started", "cycle_id": cycle.id}

@router.get("/cycles", response_model=list[schemas.ReviewCycle])
def list_cycles(db: Session = Depends(get_db)):
    return db.query(models.ReviewCycle).order_by(models.ReviewCycle.created_at.desc()).all()

@router.get("/items", response_model=list[schemas.ReviewItemBase])
def list_items(cycle_id: int, db: Session = Depends(get_db)):
    return db.query(models.ReviewItem).filter(models.ReviewItem.cycle_id == cycle_id).all()

# Stage-specific "my items"
@router.get("/reporting-manager/items", response_model=list[schemas.ReviewItemBase])
def rm_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    return db.query(models.ReviewItem).filter(
        models.ReviewItem.cycle_id == cycle_id,
        models.ReviewItem.reporting_manager_id == user_id,
        models.ReviewItem.pending_stage == "reporting_manager",
    ).all()

@router.get("/app-manager/items", response_model=list[schemas.ReviewItemBase])
def am_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    return db.query(models.ReviewItem).filter(
        models.ReviewItem.cycle_id == cycle_id,
        models.ReviewItem.app_manager_id == user_id,
        models.ReviewItem.pending_stage == "app_manager",
    ).all()

@router.get("/app-owner/items", response_model=list[schemas.ReviewItemBase])
def ao_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    return db.query(models.ReviewItem).filter(
        models.ReviewItem.cycle_id == cycle_id,
        models.ReviewItem.app_owner_id == user_id,
        models.ReviewItem.pending_stage == "app_owner",
    ).all()

@router.get("/business-owner/items", response_model=list[schemas.ReviewItemBase])
def bo_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    return db.query(models.ReviewItem).filter(
        models.ReviewItem.cycle_id == cycle_id,
        models.ReviewItem.business_owner_id == user_id,
        models.ReviewItem.pending_stage == "business_owner",
    ).all()

# Stage actions
def _next_stage_after_rm(item: models.ReviewItem):
    if item.app_manager_id:
        return "app_manager"
    if item.app_owner_id:
        return "app_owner"
    if item.business_owner_id:
        return "business_owner"
    return "completed"

def _next_stage_after_am(item: models.ReviewItem):
    if item.app_owner_id:
        return "app_owner"
    if item.business_owner_id:
        return "business_owner"
    return "completed"

def _next_stage_after_ao(item: models.ReviewItem):
    if item.business_owner_id:
        return "business_owner"
    return "completed"

@router.post("/reporting-manager/action")
def reporting_manager_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "reporting_manager":
        raise HTTPException(400, "Item is not at reporting_manager stage")
    if item.reporting_manager_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized")

    item.manager_action = payload.action
    item.manager_comment = payload.comment
    item.manager_timestamp = datetime.utcnow()

    next_stage = _next_stage_after_rm(item)
    if next_stage == "completed":
        item.pending_stage = "completed"
        item.final_status = payload.action
    else:
        item.pending_stage = next_stage

    hist = models.ApprovalHistory(
        review_item_id=item.id,
        stage="reporting_manager",
        action=payload.action,
        comment=payload.comment,
    )
    db.add(hist)
    db.commit()
    return {"message": "Reporting manager action recorded"}

@router.post("/app-manager/action")
def app_manager_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "app_manager":
        raise HTTPException(400, "Item is not at app_manager stage")
    if item.app_manager_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized")

    item.application_manager_action = payload.action
    item.application_manager_comment = payload.comment
    item.application_manager_timestamp = datetime.utcnow()

    next_stage = _next_stage_after_am(item)
    if next_stage == "completed":
        item.pending_stage = "completed"
        item.final_status = payload.action
    else:
        item.pending_stage = next_stage

    hist = models.ApprovalHistory(
        review_item_id=item.id,
        stage="app_manager",
        action=payload.action,
        comment=payload.comment,
    )
    db.add(hist)
    db.commit()
    return {"message": "App manager action recorded"}

@router.post("/app-owner/action")
def app_owner_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "app_owner":
        raise HTTPException(400, "Item is not at app_owner stage")
    if item.app_owner_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized")

    item.application_owner_action = payload.action
    item.application_owner_comment = payload.comment
    item.application_owner_timestamp = datetime.utcnow()

    next_stage = _next_stage_after_ao(item)
    if next_stage == "completed":
        item.pending_stage = "completed"
        item.final_status = payload.action
    else:
        item.pending_stage = next_stage

    hist = models.ApprovalHistory(
        review_item_id=item.id,
        stage="app_owner",
        action=payload.action,
        comment=payload.comment,
    )
    db.add(hist)
    db.commit()
    return {"message": "App owner action recorded"}

@router.post("/business-owner/action")
def business_owner_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "business_owner":
        raise HTTPException(400, "Item is not at business_owner stage")
    if item.business_owner_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized")

    item.business_owner_action = payload.action
    item.business_owner_comment = payload.comment
    item.business_owner_timestamp = datetime.utcnow()

    item.pending_stage = "completed"
    item.final_status = payload.action

    hist = models.ApprovalHistory(
        review_item_id=item.id,
        stage="business_owner",
        action=payload.action,
        comment=payload.comment,
    )
    db.add(hist)
    db.commit()
    return {"message": "Business owner final action recorded"}
