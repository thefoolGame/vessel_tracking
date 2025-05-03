from sqlalchemy.orm import Session
from app.models.models import SensorReading
from app.schemas.sensor_reading import SensorReadingCreate

def create_sensor_reading(db: Session, reading: SensorReadingCreate):
    db_reading = SensorReading(**reading.dict())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading

def get_sensor_reading(db: Session, reading_id: int):
    return db.query(SensorReading).get(reading_id)

def get_sensor_readings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SensorReading).offset(skip).limit(limit).all()
