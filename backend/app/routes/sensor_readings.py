from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.sensor_reading import SensorReadingCreate, SensorReadingResponse
from app.crud import sensor_readings as crud
from typing import List

router = APIRouter(prefix="/sensor_readings", tags=["sensor_readings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=SensorReadingResponse)
def create(reading: SensorReadingCreate, db: Session = Depends(get_db)):
    return crud.create_sensor_reading(db, reading)

@router.get("/{reading_id}", response_model=SensorReadingResponse)
def read(reading_id: int, db: Session = Depends(get_db)):
    reading = crud.get_sensor_reading(db, reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading

@router.get("/", response_model=List[SensorReadingResponse])
def read_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_sensor_readings(db, skip, limit)
