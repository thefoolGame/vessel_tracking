from sqlalchemy.orm import Session
from app.models.models import WeatherData
from app.schemas.weather import WeatherDataCreate
from geoalchemy2.shape import from_shape
from shapely import wkt
from fastapi import HTTPException

def create_weather_data(db: Session, weather: WeatherDataCreate):
    try:
        location_geom = from_shape(wkt.loads(weather.location_wkt), srid=4326)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid WKT format")

    db_weather = WeatherData(
        location=location_geom,
        **weather.dict(exclude={"location_wkt"})
    )
    db.add(db_weather)
    db.commit()
    db.refresh(db_weather)
    return db_weather

def get_weather_data(db: Session, weather_data_id: int):
    return db.query(WeatherData).get(weather_data_id)

def get_weather_data_list(db: Session, skip: int = 0, limit: int = 100):
    return db.query(WeatherData).offset(skip).limit(limit).all()
