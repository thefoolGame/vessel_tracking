from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.location import LocationCreate, LocationResponse
from app.crud import locations as crud
from typing import List

router = APIRouter(prefix="/locations", tags=["locations"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=LocationResponse)
def create_location(location: LocationCreate, db: Session = Depends(get_db)):
    return crud.create_location(db, location)

@router.get("/{location_id}", response_model=LocationResponse)
def read_location(location_id: int, db: Session = Depends(get_db)):
    location = crud.get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.get("/", response_model=List[LocationResponse])
def read_all_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_locations(db=db, skip=skip, limit=limit)
