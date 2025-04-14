from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.sensor import SensorCreate, SensorResponse
from app.crud import sensors as crud_sensors

router = APIRouter(prefix="/sensors", tags=["sensors"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=SensorResponse)
def create_sensor(sensor: SensorCreate, db: Session = Depends(get_db)):
    return crud_sensors.create_sensor(db, sensor)

@router.get("/", response_model=List[SensorResponse])
def read_sensors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_sensors.get_sensors(db, skip, limit)
