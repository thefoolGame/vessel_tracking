from sqlalchemy.orm import Session
from app.models.models import MaintenanceRecord, Vessel
from app.schemas.maintenance import MaintenanceCreate
from fastapi import HTTPException

def create_maintenance(db: Session, maintenance: MaintenanceCreate):
    if not db.query(Vessel).get(maintenance.vessel_id):
        raise HTTPException(status_code=400, detail="Vessel does not exist")
    db_record = MaintenanceRecord(**maintenance.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_maintenance(db: Session, maintenance_id: int):
    return db.query(MaintenanceRecord).get(maintenance_id)

def get_maintenance_list(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MaintenanceRecord).offset(skip).limit(limit).all()
