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
    try:
        return crud_sensor_class.create_sensor_class(db=db, sensor_class=sensor_class)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[SensorClassResponse])
def read_all_sensor_classes(
    skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)
):
    return crud_sensor_class.get_sensor_classes(db, skip=skip, limit=limit)


@router.get("/{sensor_class_id}", response_model=SensorClassResponse)
def read_single_sensor_class(sensor_class_id: int, db: Session = Depends(get_db)):
    db_sensor_class = crud_sensor_class.get_sensor_class(
        db, sensor_class_id=sensor_class_id
    )
    if db_sensor_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor Class not found"
        )
    return db_sensor_class


@router.put("/{sensor_class_id}", response_model=SensorClassResponse)
def update_existing_sensor_class(
    sensor_class_id: int,
    sensor_class_update: SensorClassUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated_sensor_class = crud_sensor_class.update_sensor_class(
            db=db,
            sensor_class_id=sensor_class_id,
            sensor_class_update=sensor_class_update,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if updated_sensor_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor Class not found"
        )
    return updated_sensor_class


@router.delete("/{sensor_class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_sensor_class(sensor_class_id: int, db: Session = Depends(get_db)):
    try:
        deleted = crud_sensor_class.delete_sensor_class(
            db, sensor_class_id=sensor_class_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sensor Class not found"
            )
    except (
        Exception
    ) as e:  # Przechwyć błędy z CRUD (np. IntegrityError, jeśli są zależności)
        # Można by bardziej szczegółowo rozróżniać błędy
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Could not delete sensor class: {str(e)}",
        )
    return None
