from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import SessionLocal

from app.schemas.sensor import (
    SensorCreate,
    SensorUpdate,
    SensorResponse,
)
from app.crud import sensors as crud_sensor
from app.crud import vessels as crud_vessel

router = APIRouter(
    prefix="/vessels/{vessel_id}/sensors",
    tags=["Vessel Sensors"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_vessel_exists(db: Session, vessel_id: int):
    db_vessel = crud_vessel.get_vessel(db, vessel_id=vessel_id)
    if not db_vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with id {vessel_id} not found.",
        )
    return db_vessel


@router.post(
    "/",  # /vessels/{vessel_id}/sensors/
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sensor for a specific vessel",
)
def create_sensor(
    vessel_id: int,  # Pobierane z prefiksu routera
    sensor_in: SensorCreate,
    db: Session = Depends(get_db),
):
    check_vessel_exists(db, vessel_id)  # Sprawdzenie istnienia statku
    try:
        return crud_sensor.create_sensor_for_vessel(
            db=db, sensor_in=sensor_in, vessel_id=vessel_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/",
    response_model=List[SensorResponse],
    summary="List all sensors for a specific vessel",
)
def list_sensors_for_vessel(
    vessel_id: int,  # Pobierane z prefiksu routera
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    check_vessel_exists(db, vessel_id)  # Sprawdzenie istnienia statku
    sensors = crud_sensor.get_sensors_for_vessel(
        db=db, vessel_id=vessel_id, skip=skip, limit=limit
    )
    return sensors


@router.get(
    "/{sensor_id}",  # Ścieżka: /vessels/{vessel_id}/sensors/{sensor_id}
    response_model=SensorResponse,
    summary="Get a specific sensor by its ID for a specific vessel",
)
def read_sensor(
    vessel_id: int,  # Pobierane z prefiksu routera
    sensor_id: int,
    db: Session = Depends(get_db),
):
    # check_vessel_exists(db, vessel_id) # Można dodać dla pewności, ale get_sensor też to weryfikuje
    db_sensor = crud_sensor.get_sensor(db=db, sensor_id=sensor_id, vessel_id=vessel_id)
    if db_sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found on vessel {vessel_id}.",
        )
    return db_sensor


@router.put(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Update a sensor for a specific vessel",
)
def update_existing_sensor(
    vessel_id: int,  # Pobierane z prefiksu routera
    sensor_id: int,
    sensor_in: SensorUpdate,
    db: Session = Depends(get_db),
):
    check_vessel_exists(db, vessel_id)  # Sprawdzenie istnienia statku
    try:
        updated_sensor = crud_sensor.update_sensor(
            db=db,
            sensor_id=sensor_id,
            sensor_in=sensor_in,
            vessel_id=vessel_id,
        )
        if updated_sensor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor with id {sensor_id} not found on vessel {vessel_id} for update.",
            )
        return updated_sensor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sensor from a specific vessel",
)
def delete_existing_sensor(
    vessel_id: int,  # Pobierane z prefiksu routera
    sensor_id: int,
    db: Session = Depends(get_db),
):
    check_vessel_exists(db, vessel_id)  # Sprawdzenie istnienia statku
    try:
        deleted_sensor = crud_sensor.delete_sensor(
            db=db, sensor_id=sensor_id, vessel_id=vessel_id
        )
        if deleted_sensor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor with id {sensor_id} not found on vessel {vessel_id} for deletion.",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    return None
