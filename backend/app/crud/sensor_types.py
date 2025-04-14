from sqlalchemy.orm import Session
from app.models.models import SensorType, SensorClass, Manufacturer
from app.schemas.sensor_type import SensorTypeCreate
from fastapi import HTTPException

def create_sensor_type(db: Session, sensor_type: SensorTypeCreate):
    # Walidacja istnienia SensorClass
    sensor_class = db.query(SensorClass).get(sensor_type.sensor_class_id)
    if not sensor_class:
        raise HTTPException(status_code=400, detail="SensorClass does not exist")

    # Walidacja istnienia Manufacturer (opcjonalnie)
    if sensor_type.manufacturer_id:
        manufacturer = db.query(Manufacturer).get(sensor_type.manufacturer_id)
        if not manufacturer:
            raise HTTPException(status_code=400, detail="Manufacturer does not exist")

    db_obj = SensorType(**sensor_type.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_sensor_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SensorType).offset(skip).limit(limit).all()
