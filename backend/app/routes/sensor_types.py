from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.schemas.sensor_type import (
    SensorTypeCreate,
    SensorTypeUpdate,
    SensorTypeResponse,
)
from app.crud import sensor_types as crud_sensor_type

router = APIRouter(prefix="/sensor-types", tags=["Sensor Types"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/", response_model=SensorTypeResponse, status_code=status.HTTP_201_CREATED
)
def create_new_sensor_type(
    sensor_type: SensorTypeCreate, db: Session = Depends(get_db)
):
    try:
        return crud_sensor_type.create_sensor_type(db=db, sensor_type=sensor_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[SensorTypeResponse])
def read_all_sensor_types(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud_sensor_type.get_sensor_types(db, skip=skip, limit=limit)


@router.get("/{sensor_type_id}", response_model=SensorTypeResponse)
def read_single_sensor_type(sensor_type_id: int, db: Session = Depends(get_db)):
    db_sensor_type = crud_sensor_type.get_sensor_type(db, sensor_type_id=sensor_type_id)
    if db_sensor_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor Type not found"
        )
    return db_sensor_type


@router.put("/{sensor_type_id}", response_model=SensorTypeResponse)
def update_existing_sensor_type(
    sensor_type_id: int,
    sensor_type_update: SensorTypeUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated_sensor_type = crud_sensor_type.update_sensor_type(
            db=db, sensor_type_id=sensor_type_id, sensor_type_update=sensor_type_update
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if updated_sensor_type is None:  # Jeśli CRUD zwrócił None, bo nie znalazł
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor Type not found"
        )
    return updated_sensor_type


@router.delete("/{sensor_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_sensor_type(sensor_type_id: int, db: Session = Depends(get_db)):
    try:
        deleted_sensor_type = crud_sensor_type.delete_sensor_type(
            db, sensor_type_id=sensor_type_id
        )
        if not deleted_sensor_type:  # Jeśli CRUD zwrócił None, bo nie znalazł
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Sensor Type not found"
            )
    except ValueError as e:  # Błąd z CRUD (np. nie można usunąć z powodu zależności)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return None  # Dla 204 No Content
