from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.schemas.maintenance import MaintenanceCreate, MaintenanceResponse
from app.crud import maintenance as crud_maintenance

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=MaintenanceResponse)
def create_maintenance(maintenance: MaintenanceCreate, db: Session = Depends(get_db)):
    return crud_maintenance.create_maintenance(db=db, maintenance=maintenance)

@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def read_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    db_record = crud_maintenance.get_maintenance(db, maintenance_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return db_record

@router.get("/", response_model=List[MaintenanceResponse])
def read_maintenance_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_maintenance.get_maintenance_list(db=db, skip=skip, limit=limit)
