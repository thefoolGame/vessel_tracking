from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.schemas.sensor_reading import (
    SensorReadingCreate,
    SensorReadingResponse,
)
from app.crud import sensor_readings as crud_sensor_reading
from app.crud import sensors as crud_sensor
from app.crud import vessels as crud_vessel

from app.core.database import SessionLocal


router = APIRouter(
    prefix="/sensors/{sensor_id}/readings",  # Zagnieżdżony pod sensorem
    tags=["Sensor Readings Ingestion"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",  # Pełna ścieżka: /sensors/{sensor_id}/readings/
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new sensor reading (for data ingestion systems)",
)
def submit_sensor_reading(
    sensor_id: int,
    reading_in: SensorReadingCreate,
    db: Session = Depends(get_db),
):
    db_sensor = crud_sensor.get_sensor(db, sensor_id=sensor_id)
    if not db_sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found",
        )
    try:
        return crud_sensor_reading.create_sensor_reading(
            db=db, reading_in=reading_in, sensor_id=sensor_id
        )
    except ValueError as e:  # Błędy z CRUD (np. sensor nie istnieje, zły status)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/",  # Pełna ścieżka: /sensors/{sensor_id}/readings/
    response_model=List[SensorReadingResponse],
    summary="Get sensor readings for a specific sensor (public)",
)
def public_get_readings_for_sensor(
    sensor_id: int,
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    # Sprawdź, czy sensor istnieje, aby zwrócić 404, jeśli nie
    db_sensor = crud_sensor.get_sensor(db, sensor_id=sensor_id)
    if not db_sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found",
        )

    readings = crud_sensor_reading.get_sensor_readings(
        db=db,
        sensor_id=sensor_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )
    return readings
