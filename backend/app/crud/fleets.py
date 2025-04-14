from sqlalchemy.orm import Session
from app.models.models import Fleet, Operator
from app.schemas.fleet import FleetCreate
from fastapi import HTTPException

def create_fleet(db: Session, fleet: FleetCreate):
    operator = db.query(Operator).get(fleet.operator_id)
    if not operator:
        raise HTTPException(status_code=400, detail="Operator does not exist")
    db_fleet = Fleet(**fleet.dict())
    db.add(db_fleet)
    db.commit()
    db.refresh(db_fleet)
    return db_fleet

def get_fleet(db: Session, fleet_id: int):
    return db.query(Fleet).get(fleet_id)

def get_fleets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Fleet).offset(skip).limit(limit).all()
