from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.schemas.weather import WeatherDataCreate, WeatherDataResponse
from app.crud import weather as crud_weather

router = APIRouter(prefix="/weather", tags=["weather"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=WeatherDataResponse)
def create_weather(weather: WeatherDataCreate, db: Session = Depends(get_db)):
    return crud_weather.create_weather_data(db=db, weather=weather)

@router.get("/{weather_data_id}", response_model=WeatherDataResponse)
def read_weather(weather_data_id: int, db: Session = Depends(get_db)):
    db_weather = crud_weather.get_weather_data(db, weather_data_id)
    if db_weather is None:
        raise HTTPException(status_code=404, detail="Weather data not found")
    return db_weather

@router.get("/", response_model=List[WeatherDataResponse])
def read_weather_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_weather.get_weather_data_list(db=db, skip=skip, limit=limit)
