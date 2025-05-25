from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.schemas.fleet import FleetCreate, FleetUpdate, FleetResponse
from app.crud import fleets as crud_fleet
from app.crud import (
    operators as crud_operator,
)  # Potrzebne do pobrania listy operatorów
from app.schemas.operator import OperatorResponse  # Potrzebne dla listy operatorów

router = APIRouter(prefix="/fleets", tags=["Fleets"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=FleetResponse, status_code=status.HTTP_201_CREATED)
def create_new_fleet(fleet_data: FleetCreate, db: Session = Depends(get_db)):
    try:
        return crud_fleet.create_fleet(db=db, fleet_data=fleet_data)
    except ValueError as e:  # Przechwyć błąd, jeśli operator nie istnieje
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[FleetResponse])
def read_fleets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    fleets = crud_fleet.get_fleets_with_vessel_counts(db, skip=skip, limit=limit)
    return fleets


@router.get("/{fleet_id}", response_model=FleetResponse)
def read_fleet(fleet_id: int, db: Session = Depends(get_db)):
    db_fleet = crud_fleet.get_fleet(db, fleet_id=fleet_id)
    if db_fleet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found"
        )
    return db_fleet


@router.put("/{fleet_id}", response_model=FleetResponse)
def update_existing_fleet(
    fleet_id: int, fleet_data: FleetUpdate, db: Session = Depends(get_db)
):
    try:
        db_fleet = crud_fleet.update_fleet(
            db=db, fleet_id=fleet_id, fleet_data=fleet_data
        )
    except ValueError as e:  # Przechwyć błąd, jeśli operator nie istnieje
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if db_fleet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found"
        )
    return db_fleet


@router.delete("/{fleet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_fleet(fleet_id: int, db: Session = Depends(get_db)):
    deleted_fleet, error_message = crud_fleet.delete_fleet(db, fleet_id=fleet_id)
    if error_message:
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=error_message
            )
    if not deleted_fleet and not error_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fleet not found or could not be processed.",
        )
    return None


# Dodatkowy endpoint do pobierania listy operatorów dla formularza
@router.get(
    "/utils/operators-for-select",
    response_model=List[OperatorResponse],
    tags=["Fleets Utils"],
)
async def get_operators_for_select(db: Session = Depends(get_db)):
    """Pobiera listę operatorów do użycia w polach select formularzy flot."""
    return crud_operator.get_operators(
        db=db, limit=1000
    )  # Załóżmy, że masz crud_operator.get_operators
