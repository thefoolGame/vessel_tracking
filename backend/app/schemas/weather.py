from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WeatherDataBase(BaseModel):
    temperature_celsius: Optional[float]
    wind_speed_knots: Optional[float]
    wind_direction_degrees: Optional[float]
    pressure_hpa: Optional[float]
    humidity_percent: Optional[float]
    precipitation_mm: Optional[float]
    visibility_km: Optional[float]
    wave_height_meters: Optional[float]
    wave_period_seconds: Optional[float]
    wave_direction_degrees: Optional[float]
    data_source: Optional[str]

class WeatherDataCreate(WeatherDataBase):
    location_wkt: str

class WeatherDataResponse(WeatherDataBase):
    weather_data_id: int
    timestamp: datetime
    location_wkt: str

    class Config:
        orm_mode = True
