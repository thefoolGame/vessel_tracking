from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.location import LocationCreate, LocationResponse, LocationUpdate
from app.schemas.vessel import VesselLatestLocationResponse
from app.crud import locations as crud_location
from app.crud import vessels as crud_vessel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/vessels/{vessel_id}/locations", tags=["Vessel Locaions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_vessel_exists_for_location(
    db: Session, vessel_id: int
):  # Inna nazwa, aby uniknąć konfliktu
    db_vessel = crud_vessel.get_vessel(db, vessel_id=vessel_id)
    if not db_vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with id {vessel_id} not found.",
        )
    return db_vessel


@router.post(
    "/",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new location entry for a specific vessel (source will be set to 'manual')",
)
def create_location(  # Nazwa funkcji create_location_entry byłaby bardziej spójna z CRUD
    vessel_id: int,
    location_in: LocationCreate,
    db: Session = Depends(get_db),
):
    # check_vessel_exists_for_location(db, vessel_id) # CRUD to sprawdza
    try:
        return crud_location.create_location_entry(
            db=db, location_in=location_in, vessel_id=vessel_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/",
    response_model=List[LocationResponse],
    summary="List location entries for a specific vessel",
)
def list_locations_for_vessel(
    vessel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),  # Zwiększony limit dla historii
    start_time: Optional[datetime] = Query(
        None, description="ISO 8601 format datetime"
    ),
    end_time: Optional[datetime] = Query(None, description="ISO 8601 format datetime"),
    db: Session = Depends(get_db),
):
    check_vessel_exists_for_location(db, vessel_id)
    locations = crud_location.get_location_entries_for_vessel(
        db=db,
        vessel_id=vessel_id,
        skip=skip,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
    )
    return locations


@router.get(
    "/latest",  # NOWY ENDPOINT
    response_model=Optional[LocationResponse],  # Może nie być żadnej lokalizacji
    summary="Get the latest location entry for a specific vessel",
)
def get_latest_location(vessel_id: int, db: Session = Depends(get_db)):
    check_vessel_exists_for_location(db, vessel_id)
    latest_location = crud_location.get_latest_location_for_vessel(
        db=db, vessel_id=vessel_id
    )
    if not latest_location:
        # Zamiast 404, można zwrócić pustą odpowiedź lub specjalny status,
        # bo brak lokalizacji niekoniecznie jest błędem "nie znaleziono zasobu".
        # Na razie zwrócimy None, co Pydantic/FastAPI obsłuży jako pusty JSON.
        return None
    return latest_location


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Get a specific location entry by its ID for a specific vessel",
)
def read_location(
    vessel_id: int,
    location_id: int,
    db: Session = Depends(get_db),
):
    # check_vessel_exists_for_location(db, vessel_id)
    db_location = crud_location.get_location_entry(
        db=db, location_id=location_id, vessel_id=vessel_id
    )
    if db_location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location entry with id {location_id} not found on vessel {vessel_id}.",
        )
    return db_location


@router.put(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Update a location entry (source will be set to 'manual')",
)
def update_existing_location(
    vessel_id: int,
    location_id: int,
    location_in: LocationUpdate,
    db: Session = Depends(get_db),
):
    # check_vessel_exists_for_location(db, vessel_id)
    try:
        updated_location = crud_location.update_location_entry(
            db=db,
            location_id=location_id,
            location_in=location_in,
            vessel_id=vessel_id,
        )
        if updated_location is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location entry with id {location_id} not found on vessel {vessel_id} for update.",
            )
        return updated_location
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a location entry from a specific vessel",
)
def delete_existing_location(
    vessel_id: int,
    location_id: int,
    db: Session = Depends(get_db),
):
    # check_vessel_exists_for_location(db, vessel_id)
    try:
        deleted_location = crud_location.delete_location_entry(
            db=db, location_id=location_id, vessel_id=vessel_id
        )
        if deleted_location is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location entry with id {location_id} not found on vessel {vessel_id} for deletion.",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    return None
