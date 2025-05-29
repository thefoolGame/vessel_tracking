from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime

from app.models.models import SensorReading, Sensor  # Importuj model Sensor
from app.schemas.sensor_reading import SensorReadingCreate


def create_sensor_reading(
    db: Session, reading_in: SensorReadingCreate, sensor_id: int
) -> SensorReading:
    # 1. Sprawdź, czy sensor o podanym sensor_id istnieje
    db_sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not db_sensor:
        raise ValueError(f"Sensor with id {sensor_id} not found.")

    # 2. Utwórz obiekt SensorReading
    db_reading = SensorReading(**reading_in.model_dump(), sensor_id=sensor_id)

    try:
        db.add(db_reading)
        db.commit()
        db.refresh(db_reading)
        return db_reading
    except IntegrityError as e:  # Np. naruszenie CheckConstraint dla statusu
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        if (
            "chk_sensor_reading_status" in error_detail.lower()
        ):  # Nazwa CheckConstraint z modelu
            raise ValueError(f"Invalid status value. Detail: {error_detail}")
        raise ValueError(f"Database integrity error: {error_detail}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(
            f"An unexpected error occurred while creating sensor reading: {str(e)}"
        )


def get_sensor_readings(
    db: Session,
    sensor_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 1000,
) -> List[SensorReading]:
    db_sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not db_sensor:
        return []

    query = db.query(SensorReading).filter(SensorReading.sensor_id == sensor_id)

    if start_time:
        query = query.filter(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.filter(SensorReading.timestamp <= end_time)

    # Zazwyczaj chcemy najnowsze odczyty, ale dla wykresu lepsze jest sortowanie rosnące po czasie
    return query.order_by(SensorReading.timestamp.asc()).offset(skip).limit(limit).all()


def get_sensor_readings_for_vessel(
    db: Session,
    vessel_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sensor_ids: Optional[
        List[int]
    ] = None,  # Filtrowanie po konkretnych sensorach na statku
    skip: int = 0,
    limit: int = 10000,
) -> List[SensorReading]:
    query = db.query(SensorReading).join(Sensor).filter(Sensor.vessel_id == vessel_id)

    if start_time:
        query = query.filter(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.filter(SensorReading.timestamp <= end_time)
    if sensor_ids:
        query = query.filter(SensorReading.sensor_id.in_(sensor_ids))

    return (
        query.order_by(SensorReading.sensor_id, SensorReading.timestamp.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
