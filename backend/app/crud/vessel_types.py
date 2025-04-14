from sqlalchemy.orm import Session
from app.models.models import VesselType, Manufacturer
from app.schemas.vessel_type import VesselTypeCreate
from fastapi import HTTPException

def create_vessel_type(db: Session, vessel_type: VesselTypeCreate):
    manufacturer = db.query(Manufacturer).get(vessel_type.manufacturer_id)
    if not manufacturer:
        raise HTTPException(status_code=400, detail="Manufacturer does not exist")
    db_vessel_type = VesselType(**vessel_type.dict())
    db.add(db_vessel_type)
    db.commit()
    db.refresh(db_vessel_type)
    return db_vessel_type

def get_vessel_type(db: Session, vessel_type_id: int):
    return db.query(VesselType).get(vessel_type_id)

def get_vessel_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(VesselType).offset(skip).limit(limit).all()
