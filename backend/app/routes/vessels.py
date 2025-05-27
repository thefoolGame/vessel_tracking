# app/routes/vessels.py (w głównym API backendu)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.vessel import (
    VesselCreate,
    VesselUpdate,
    VesselResponse,
    VesselSensorConfigurationStatusResponse,
)
from app.crud import vessels as crud_vessel
from app.core.database import SessionLocal

router = APIRouter(prefix="/vessels", tags=["Vessels"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=VesselResponse, status_code=status.HTTP_201_CREATED)
def create_new_vessel(vessel_in: VesselCreate, db: Session = Depends(get_db)):
    try:
        return crud_vessel.create_vessel(db=db, vessel=vessel_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/", response_model=List[VesselResponse])
def read_all_vessels(
    skip: int = 0,
    limit: int = 100,
    fleet_id: Optional[int] = Query(None),
    operator_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    if fleet_id is not None:
        return crud_vessel.get_vessels_by_fleet(
            db, fleet_id=fleet_id, skip=skip, limit=limit
        )
    if operator_id is not None:
        return crud_vessel.get_vessels_by_operator(
            db, operator_id=operator_id, skip=skip, limit=limit
        )
    return crud_vessel.get_vessels(db, skip=skip, limit=limit)


@router.get("/{vessel_id}", response_model=VesselResponse)
def read_single_vessel(vessel_id: int, db: Session = Depends(get_db)):
    db_vessel = crud_vessel.get_vessel(db, vessel_id=vessel_id)
    if db_vessel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found"
        )
    return db_vessel


@router.put("/{vessel_id}", response_model=VesselResponse)
def update_existing_vessel(
    vessel_id: int, vessel_in: VesselUpdate, db: Session = Depends(get_db)
):
    try:
        updated_vessel = crud_vessel.update_vessel(
            db=db, vessel_id=vessel_id, vessel_update=vessel_in
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    if (
        updated_vessel is None
    ):  # Jeśli CRUD zwrócił None, a nie rzucił wyjątku (co nie powinno się zdarzyć)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found for update"
        )
    return updated_vessel


@router.delete("/{vessel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_vessel(vessel_id: int, db: Session = Depends(get_db)):
    try:
        deleted_vessel = crud_vessel.delete_vessel(db, vessel_id=vessel_id)
        if not deleted_vessel:  # Jeśli CRUD zwrócił None (nie znaleziono)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found"
            )
    except ValueError as e:  # Np. błąd integralności z CRUD
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return None


@router.get(
    "/{vessel_id}/sensor-configuration-status",
    response_model=VesselSensorConfigurationStatusResponse,
    summary="Get sensor configuration status for a specific vessel",
    description="Retrieves the list of allowed sensor classes (required and optional) for the vessel's type, "
    "along with the current installation status of sensors.",
)
def read_vessel_sensor_configuration_status(
    vessel_id: int, db: Session = Depends(get_db)
):
    # Sprawdź najpierw, czy statek istnieje, aby dać 404 jeśli nie
    db_vessel = crud_vessel.get_vessel(db, vessel_id=vessel_id)
    if db_vessel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with id {vessel_id} not found.",
        )

    status_response = crud_vessel.get_vessel_sensor_configuration_status(
        db=db, vessel_id=vessel_id
    )
    # Funkcja CRUD powinna zwrócić None tylko jeśli statek nie istnieje,
    # co już sprawdziliśmy. Jeśli vessel_type nie istnieje, funkcja CRUD
    # powinna zwrócić odpowiednio wypełniony obiekt.
    if status_response is None:
        # Ten przypadek nie powinien się zdarzyć, jeśli statek istnieje
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve sensor configuration status.",
        )
    return status_response
