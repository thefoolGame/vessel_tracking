from sqlalchemy.orm import Session
from app.models.models import VesselParameter, Vessel
from app.schemas.vessel_parameter import VesselParameterCreate
from fastapi import HTTPException

def create_vessel_parameter(db: Session, param: VesselParameterCreate):
    if not db.query(Vessel).get(param.vessel_id):
        raise HTTPException(status_code=400, detail="Vessel does not exist")
    db_param = VesselParameter(**param.dict())
    db.add(db_param)
    db.commit()
    db.refresh(db_param)
    return db_param

def get_vessel_parameter(db: Session, parameter_id: int):
    return db.query(VesselParameter).get(parameter_id)

def get_vessel_parameters(db: Session, skip: int = 0, limit: int = 100):
    return db.query(VesselParameter).offset(skip).limit(limit).all()
