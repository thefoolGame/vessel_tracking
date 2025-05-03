from sqlalchemy.orm import Session
from app.models.models import Alert, Vessel
from app.schemas.alert import AlertCreate
from fastapi import HTTPException

def create_alert(db: Session, alert: AlertCreate):
    if not db.query(Vessel).get(alert.vessel_id):
        raise HTTPException(status_code=400, detail="Vessel does not exist")
    db_alert = Alert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def get_alert(db: Session, alert_id: int):
    return db.query(Alert).get(alert_id)

def get_alerts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Alert).offset(skip).limit(limit).all()
