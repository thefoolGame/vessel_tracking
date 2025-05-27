from app.core.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.sensor_class import (
    SensorClassCreate,
    SensorClassUpdate,
    SensorClassResponse,
)
from app.crud import sensor_classes as crud_sensor_class

router = APIRouter(prefix="/sensor-classes", tags=["Sensor Classes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/", response_model=SensorClassResponse, status_code=status.HTTP_201_CREATED
)
def create_new_sensor_class(
    sensor_class: SensorClassCreate, db: Session = Depends(get_db)
):
    created_sensor_class, error_message = crud_sensor_class.create_sensor_class(
        db=db, sensor_class=sensor_class
    )
    if error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_message
        )
    if not created_sensor_class:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create sensor class",
        )
    return created_sensor_class


@router.get("/", response_model=List[SensorClassResponse])
def read_all_sensor_classes(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    sensor_classes = crud_sensor_class.get_sensor_classes(db, skip=skip, limit=limit)
    return sensor_classes


@router.get("/{sensor_class_id}", response_model=SensorClassResponse)
def read_single_sensor_class(sensor_class_id: int, db: Session = Depends(get_db)):
    db_sensor_class = crud_sensor_class.get_sensor_class(
        db, sensor_class_id=sensor_class_id
    )
    if db_sensor_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor class not found"
        )
    return db_sensor_class


@router.put("/{sensor_class_id}", response_model=SensorClassResponse)
def update_existing_sensor_class(
    sensor_class_id: int,
    sensor_class_in: SensorClassUpdate,
    db: Session = Depends(get_db),
):
    updated_sensor_class, error_message = crud_sensor_class.update_sensor_class(
        db=db, sensor_class_id=sensor_class_id, sensor_class_update=sensor_class_in
    )
    if error_message:
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_message
            )
        else:  # Inny błąd, np. konflikt nazwy
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_message
            )
    if not updated_sensor_class:  # Dodatkowe zabezpieczenie
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update sensor class",
        )
    return updated_sensor_class


@router.delete("/{sensor_class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_sensor_class(sensor_class_id: int, db: Session = Depends(get_db)):
    deleted_info, error_message = crud_sensor_class.delete_sensor_class(
        db, sensor_class_id=sensor_class_id
    )
    if error_message:
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_message
            )
        else:  # Np. błąd zależności
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=error_message
            )
    if not deleted_info and not error_message:  # Dodatkowe zabezpieczenie
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor class not found or could not be processed.",
        )
    return None  # Dla 204 No Content
