from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.vessel import VesselCreate, VesselResponse
from app.crud import vessels as crud_vessels
from app.core.database import SessionLocal
from typing import List

router = APIRouter(prefix="/vessels", tags=["vessels"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=VesselResponse)
def create_vessel(vessel: VesselCreate, db: Session = Depends(get_db)):
    return crud_vessels.create_vessel(db=db, vessel=vessel)

@router.get("/{vessel_id}", response_model=VesselResponse)
def read_vessel(vessel_id: int, db: Session = Depends(get_db)):
    db_vessel = crud_vessels.get_vessel(db, vessel_id=vessel_id)
    if db_vessel is None:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return db_vessel

@router.get("/", response_model=List[VesselResponse])
def read_vessels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_vessels.get_vessels(db=db, skip=skip, limit=limit)