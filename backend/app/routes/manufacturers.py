from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.manufacturer import (
    ManufacturerCreate,
    ManufacturerResponse,
    ManufacturerUpdate,
)
from app.crud import manufacturers as crud_manufacturer
from typing import List

router = APIRouter(prefix="/manufacturers", tags=["Manufacturers"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/", response_model=ManufacturerResponse, status_code=status.HTTP_201_CREATED
)
def create_new_manufacturer(
    manufacturer: ManufacturerCreate,
    db: Session = Depends(get_db),
):
    return crud_manufacturer.create_manufacturer(db=db, manufacturer=manufacturer)


@router.get("/{manufacturer_id}", response_model=ManufacturerResponse)
def read_manufacturer(
    manufacturer_id: int,
    db: Session = Depends(get_db),
):
    db_manufacturer = crud_manufacturer.get_manufacturer(
        db, manufacturer_id=manufacturer_id
    )
    if db_manufacturer is None:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return db_manufacturer


@router.get("/", response_model=List[ManufacturerResponse])
def read_manufacturers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    manufacturers = crud_manufacturer.get_manufacturers(db, skip=skip, limit=limit)
    return manufacturers


@router.put("/{manufacturer_id}", response_model=ManufacturerResponse)
def update_existing_manufacturer(
    manufacturer_id: int,
    manufacturer_update_data: ManufacturerUpdate,
    db: Session = Depends(get_db),
):
    db_manufacturer = crud_manufacturer.update_manufacturer(
        db=db,
        manufacturer_id=manufacturer_id,
        manufacturer_update=manufacturer_update_data,
    )
    if db_manufacturer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Manufacturer not found"
        )
    return db_manufacturer


@router.delete(
    "/{manufacturer_id}", status_code=status.HTTP_204_NO_CONTENT
)  # Zmieniono na 204 dla sukcesu bez treści
def delete_existing_manufacturer(
    manufacturer_id: int,
    db: Session = Depends(get_db),
):
    deleted_manufacturer, error_message = crud_manufacturer.delete_manufacturer(
        db, manufacturer_id=manufacturer_id
    )

    if error_message:
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=error_message
            )
    return None
