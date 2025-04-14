from sqlalchemy.orm import Session
from app.models.models import Sensor, SensorType, Vessel
from app.schemas.sensor import SensorCreate
from fastapi import HTTPException

def create_sensor(db: Session, sensor: SensorCreate):
    # Walidacja istnienia SensorType
    sensor_type = db.query(SensorType).get(sensor.sensor_type_id)
    if not sensor_type:
        raise HTTPException(status_code=400, detail="SensorType does not exist")

    # Walidacja istnienia Vessel
    vessel = db.query(Vessel).get(sensor.vessel_id)
    if not vessel:
        raise HTTPException(status_code=400, detail="Vessel does not exist")

    db_obj = Sensor(**sensor.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_sensors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Sensor).offset(skip).limit(limit).all()
