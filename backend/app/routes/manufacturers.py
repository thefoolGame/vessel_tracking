from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerResponse
from app.crud import manufacturers as crud_manufacturers
from typing import List

router = APIRouter(prefix="/manufacturers", tags=["manufacturers"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ManufacturerResponse)
def create_manufacturer(manufacturer: ManufacturerCreate, db: Session = Depends(get_db)):
    return crud_manufacturers.create_manufacturer(db=db, manufacturer=manufacturer)

@router.get("/{manufacturer_id}", response_model=ManufacturerResponse)
def read_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    db_manufacturer = crud_manufacturers.get_manufacturer(db, manufacturer_id=manufacturer_id)
    if db_manufacturer is None:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return db_manufacturer

@router.get("/", response_model=List[ManufacturerResponse])
def read_manufacturers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_manufacturers.get_manufacturers(db=db, skip=skip, limit=limit)