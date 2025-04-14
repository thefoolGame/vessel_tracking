from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.sensor_class import SensorClassCreate, SensorClassResponse
from app.crud import sensor_classes as crud_sensor_classes

router = APIRouter(prefix="/sensor_classes", tags=["sensor_classes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=SensorClassResponse)
def create_sensor_class(sensor_class: SensorClassCreate, db: Session = Depends(get_db)):
    return crud_sensor_classes.create_sensor_class(db, sensor_class)

@router.get("/", response_model=List[SensorClassResponse])
def read_sensor_classes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_sensor_classes.get_sensor_classes(db, skip, limit)
