from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.fleet import FleetCreate, FleetResponse
from app.crud import fleets as crud_fleets
from typing import List

router = APIRouter(prefix="/fleets", tags=["fleets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=FleetResponse)
def create_fleet(fleet: FleetCreate, db: Session = Depends(get_db)):
    return crud_fleets.create_fleet(db=db, fleet=fleet)

@router.get("/{fleet_id}", response_model=FleetResponse)
def read_fleet(fleet_id: int, db: Session = Depends(get_db)):
    db_fleet = crud_fleets.get_fleet(db, fleet_id=fleet_id)
    if db_fleet is None:
        raise HTTPException(status_code=404, detail="Fleet not found")
    return db_fleet

@router.get("/", response_model=List[FleetResponse])
def read_fleets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_fleets.get_fleets(db=db, skip=skip, limit=limit)