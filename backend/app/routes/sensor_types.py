from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.sensor_type import SensorTypeCreate, SensorTypeResponse
from app.crud import sensor_types as crud_sensor_types

router = APIRouter(prefix="/sensor_types", tags=["sensor_types"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=SensorTypeResponse)
def create_sensor_type(sensor_type: SensorTypeCreate, db: Session = Depends(get_db)):
    return crud_sensor_types.create_sensor_type(db, sensor_type)

@router.get("/", response_model=List[SensorTypeResponse])
def read_sensor_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_sensor_types.get_sensor_types(db, skip, limit)
