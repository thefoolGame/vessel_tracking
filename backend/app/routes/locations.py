from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.location import LocationCreate, LocationResponse
from app.schemas.vessel import VesselLatestLocationResponse
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


@router.get("/", response_model=List[LocationResponse])
def read_all_locations(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    return crud.get_all_locations(db=db, skip=skip, limit=limit)


@router.get("/vessel/{vessel_id}", response_model=List[LocationResponse])
def read_vessel_locations(
    vessel_id: int, limit: int = 1000, db: Session = Depends(get_db)
):
    locations = crud.get_locations_by_vessel_id(db, vessel_id, limit)
    if not locations:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return locations


@router.get("/latest-positions", response_model=List[VesselLatestLocationResponse])
def get_latest_vessel_positions_for_map(db: Session = Depends(get_db)):
    """
    Zwraca listę wszystkich statków z ich najnowszą znaną pozycją,
    nazwą i przedostatnią pozycją.
    """
    latest_positions_data = crud.get_latest_location_for_each_vessel(db)

    return latest_positions_data
