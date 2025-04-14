from sqlalchemy.orm import Session
from app.models.models import SensorClass
from app.schemas.sensor_class import SensorClassCreate

def create_sensor_class(db: Session, sensor_class: SensorClassCreate):
    db_obj = SensorClass(**sensor_class.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_sensor_classes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SensorClass).offset(skip).limit(limit).all()
