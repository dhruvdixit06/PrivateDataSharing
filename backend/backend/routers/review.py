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
        rm_map = db.query(models.ReportingMap).filter(models.ReportingMap.user_id == acc.user_id).first()
        reporting_manager_id = rm_map.manager_id if rm_map else None

        if reporting_manager_id:
            rm_app = db.query(models.ReportingAppMap).filter(models.ReportingAppMap.manager_id == reporting_manager_id, models.ReportingAppMap.app_id == acc.application_id).first()
            if not rm_app:
                reporting_manager_id = None

        am_map = db.query(models.AppManagerMap).filter(models.AppManagerMap.app_id == acc.application_id).first()
        app_manager_id = am_map.user_id if am_map else None

        ao_map = db.query(models.AppOwnerMap).filter(models.AppOwnerMap.app_id == acc.application_id).first()
        app_owner_id = ao_map.user_id if ao_map else None

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


@router.get("/reporting-manager/items", response_model=list[schemas.ReviewItemBase])
def get_rm_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    items = db.query(models.ReviewItem).filter(models.ReviewItem.cycle_id == cycle_id, models.ReviewItem.reporting_manager_id == user_id, models.ReviewItem.pending_stage == "reporting_manager").all()
    return items

@router.get("/app-manager/items", response_model=list[schemas.ReviewItemBase])
def get_app_mgr_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    items = db.query(models.ReviewItem).filter(models.ReviewItem.cycle_id == cycle_id, models.ReviewItem.app_manager_id == user_id, models.ReviewItem.pending_stage == "app_manager").all()
    return items

@router.get("/app-owner/items", response_model=list[schemas.ReviewItemBase])
def get_app_owner_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    items = db.query(models.ReviewItem).filter(models.ReviewItem.cycle_id == cycle_id, models.ReviewItem.app_owner_id == user_id, models.ReviewItem.pending_stage == "app_owner").all()
    return items

@router.get("/business-owner/items", response_model=list[schemas.ReviewItemBase])
def get_bo_items(user_id: int, cycle_id: int, db: Session = Depends(get_db)):
    items = db.query(models.ReviewItem).filter(models.ReviewItem.cycle_id == cycle_id, models.ReviewItem.business_owner_id == user_id, models.ReviewItem.pending_stage == "business_owner").all()
    return items


@router.post("/reporting-manager/action")
def reporting_manager_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "reporting_manager":
        raise HTTPException(400, "Item is not at Reporting Manager stage")
    if item.reporting_manager_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized for this item")

    item.manager_action = payload.action
    item.manager_comment = payload.comment
    item.manager_timestamp = datetime.utcnow()

    staging = db.query(models.StagingChange).filter(models.StagingChange.review_item_id == item.id, models.StagingChange.applied == False).first()
    if staging is None:
        staging = models.StagingChange(review_item_id=item.id, proposed_action=payload.action, proposed_by_id=payload.actor_user_id, payload=payload.comment or None, last_stage="reporting_manager")
        db.add(staging)
    else:
        staging.proposed_action = payload.action
        staging.payload = payload.comment or staging.payload
        staging.proposed_by_id = payload.actor_user_id
        staging.last_stage = "reporting_manager"
        staging.proposed_at = datetime.utcnow()

    if item.app_manager_id:
        item.pending_stage = "app_manager"
    elif item.app_owner_id:
        item.pending_stage = "app_owner"
    elif item.business_owner_id:
        item.pending_stage = "business_owner"
    else:
        item.pending_stage = "completed"
        item.final_status = payload.action

    db.commit()
    return {"message": "Reporting manager action recorded and staging saved"}


@router.post("/app-manager/action")
def app_manager_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "app_manager":
        raise HTTPException(400, "Item is not at Application Manager stage")
    if item.app_manager_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized for this item")

    item.application_manager_action = payload.action
    item.application_manager_comment = payload.comment
    item.application_manager_timestamp = datetime.utcnow()

    staging = db.query(models.StagingChange).filter(models.StagingChange.review_item_id == item.id, models.StagingChange.applied == False).first()
    if staging is None:
        staging = models.StagingChange(review_item_id=item.id, proposed_action=payload.action, proposed_by_id=payload.actor_user_id, payload=payload.comment or None, last_stage="app_manager")
        db.add(staging)
    else:
        staging.last_stage = "app_manager"
        staging.proposed_action = payload.action
        staging.payload = payload.comment or staging.payload
        staging.proposed_by_id = payload.actor_user_id
        staging.proposed_at = datetime.utcnow()

    if item.app_owner_id:
        item.pending_stage = "app_owner"
    elif item.business_owner_id:
        item.pending_stage = "business_owner"
    else:
        item.pending_stage = "completed"
        item.final_status = payload.action

    db.commit()
    return {"message": "Application manager action recorded and staging updated"}


@router.post("/app-owner/action")
def app_owner_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "app_owner":
        raise HTTPException(400, "Item is not at Application Owner stage")
    if item.app_owner_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized for this item")

    item.application_owner_action = payload.action
    item.application_owner_comment = payload.comment
    item.application_owner_timestamp = datetime.utcnow()

    staging = db.query(models.StagingChange).filter(models.StagingChange.review_item_id == item.id, models.StagingChange.applied == False).first()
    if staging is None:
        staging = models.StagingChange(review_item_id=item.id, proposed_action=payload.action, proposed_by_id=payload.actor_user_id, payload=payload.comment or None, last_stage="app_owner")
        db.add(staging)
    else:
        staging.last_stage = "app_owner"
        staging.proposed_action = payload.action
        staging.payload = payload.comment or staging.payload
        staging.proposed_by_id = payload.actor_user_id
        staging.proposed_at = datetime.utcnow()

    if item.business_owner_id:
        item.pending_stage = "business_owner"
    else:
        item.pending_stage = "completed"
        item.final_status = payload.action

    db.commit()
    return {"message": "Application owner action recorded and staging updated"}


@router.post("/business-owner/action")
def business_owner_action(payload: schemas.StageActionInput, db: Session = Depends(get_db)):
    item = db.query(models.ReviewItem).filter(models.ReviewItem.id == payload.review_item_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")
    if item.pending_stage != "business_owner":
        raise HTTPException(400, "Item is not at Business Owner stage")
    if item.business_owner_id != payload.actor_user_id:
        raise HTTPException(403, "Not authorized for this item")

    item.business_owner_action = payload.action
    item.business_owner_comment = payload.comment
    item.business_owner_timestamp = datetime.utcnow()

    staging = db.query(models.StagingChange).filter(models.StagingChange.review_item_id == item.id, models.StagingChange.applied == False).first()

    if payload.action.lower() in ("approve", "final_approve", "apply", "retain"):
        if staging:
            acc = db.query(models.Access).filter(models.Access.id == item.access_id).first()
            if not acc:
                raise HTTPException(500, "Access record missing")
            if staging.proposed_action.lower() == "revoke":
                acc.active = False
                audit = models.AuditLog(review_item_id=item.id, action="applied_revoke", applied_by=payload.actor_user_id, details=staging.payload)
                db.add(audit)
            elif staging.proposed_action.lower() == "retain":
                audit = models.AuditLog(review_item_id=item.id, action="applied_retain", applied_by=payload.actor_user_id, details=staging.payload)
                db.add(audit)
            elif staging.proposed_action.lower() == "modify":
                import json as _json
                try:
                    payload_obj = _json.loads(staging.payload) if staging.payload else {}
                except:
                    payload_obj = {}
                if payload_obj.get("new_user_id"):
                    acc.user_id = int(payload_obj["new_user_id"])
                    audit = models.AuditLog(review_item_id=item.id, action="applied_modify_transfer", applied_by=payload.actor_user_id, details=str(payload_obj))
                    db.add(audit)
                else:
                    audit = models.AuditLog(review_item_id=item.id, action="applied_modify_noop", applied_by=payload.actor_user_id, details=staging.payload)
                    db.add(audit)
            else:
                audit = models.AuditLog(review_item_id=item.id, action=f"applied_unknown_{staging.proposed_action}", applied_by=payload.actor_user_id, details=staging.payload)
                db.add(audit)

            staging.applied = True
            staging.applied_at = datetime.utcnow()
        else:
            if payload.action.lower() in ("revoke",):
                acc = db.query(models.Access).filter(models.Access.id == item.access_id).first()
                if acc:
                    acc.active = False
                db.add(models.AuditLog(review_item_id=item.id, action="applied_direct_revoke", applied_by=payload.actor_user_id, details=payload.comment))
            else:
                db.add(models.AuditLog(review_item_id=item.id, action="applied_direct_retain", applied_by=payload.actor_user_id, details=payload.comment))

        item.pending_stage = "completed"
        item.final_status = payload.action
        db.commit()
        return {"message": "Business owner approved and staging applied (if any)"}
    else:
        item.pending_stage = "completed"
        item.final_status = payload.action
        db.add(models.AuditLog(review_item_id=item.id, action="bo_rejected", applied_by=payload.actor_user_id, details=payload.comment))
        db.commit()
        return {"message": "Business owner rejected — staging NOT applied"}
