from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.vessel_type import (
    VesselTypeCreate,
    VesselTypeUpdate,
    VesselTypeResponse,
    VesselTypeSensorRequirementCreate,
    VesselTypeSensorRequirementUpdate,
    VesselTypeSensorRequirementResponse,
)

from app.core.database import SessionLocal
from app.schemas.sensor_class import SensorClassResponse  # Do listy dostępnych klas
from app.crud import vessel_types as crud_vessel_type
from app.crud import (
    sensor_classes as crud_sensor_class,
)  # Załóżmy, że masz CRUD dla SensorClass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/vessel-types", tags=["Vessel Types"])


# --- Endpointy dla VesselType ---
@router.post(
    "/", response_model=VesselTypeResponse, status_code=status.HTTP_201_CREATED
)
def create_new_vessel_type(
    vessel_type: VesselTypeCreate, db: Session = Depends(get_db)
):
    try:
        return crud_vessel_type.create_vessel_type(db=db, vessel_type=vessel_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[VesselTypeResponse])
def read_all_vessel_types(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud_vessel_type.get_vessel_types(db, skip=skip, limit=limit)


@router.get("/{vessel_type_id}", response_model=VesselTypeResponse)
def read_single_vessel_type(vessel_type_id: int, db: Session = Depends(get_db)):
    db_vessel_type = crud_vessel_type.get_vessel_type(db, vessel_type_id=vessel_type_id)
    if db_vessel_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel Type not found"
        )
    return db_vessel_type


@router.put("/{vessel_type_id}", response_model=VesselTypeResponse)
def update_existing_vessel_type(
    vessel_type_id: int,
    vessel_type_update: VesselTypeUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated_vessel_type = crud_vessel_type.update_vessel_type(
            db=db, vessel_type_id=vessel_type_id, vessel_type_update=vessel_type_update
        )
    except ValueError as e:  # Np. jeśli producent nie istnieje
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if updated_vessel_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel Type not found"
        )
    return updated_vessel_type


@router.delete("/{vessel_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_vessel_type(vessel_type_id: int, db: Session = Depends(get_db)):
    deleted_vessel_type, error_message = crud_vessel_type.delete_vessel_type(
        db, vessel_type_id=vessel_type_id
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


# --- Endpointy dla zarządzania wymaganiami czujników dla VesselType ---


@router.get(
    "/{vessel_type_id}/sensor-requirements",
    response_model=List[VesselTypeSensorRequirementResponse],
)
def get_sensor_requirements(vessel_type_id: int, db: Session = Depends(get_db)):
    # Sprawdź, czy VesselType istnieje
    vessel_type = crud_vessel_type.get_vessel_type(db, vessel_type_id)
    if not vessel_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel Type not found"
        )

    requirements_data = crud_vessel_type.get_sensor_requirements_for_vessel_type(
        db, vessel_type_id
    )
    # Konwertuj listę słowników na listę obiektów VesselTypeSensorRequirementResponse
    response_list = []
    for req_data in requirements_data:
        response_list.append(
            VesselTypeSensorRequirementResponse(
                sensor_class_id=req_data["sensor_class_id"],
                required=req_data["required"],
                quantity=req_data["quantity"],
                sensor_class=SensorClassResponse(  # Tworzymy obiekt SensorClassResponse
                    id=req_data["sensor_class_id"],
                    name=req_data["sensor_class_name"],
                    description=req_data.get("sensor_class_description"),
                ),
            )
        )
    return response_list


@router.post(
    "/{vessel_type_id}/sensor-requirements",
    response_model=VesselTypeSensorRequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_sensor_requirement(
    vessel_type_id: int,
    requirement: VesselTypeSensorRequirementCreate,
    db: Session = Depends(get_db),
):
    try:
        new_req_data = crud_vessel_type.add_sensor_requirement_to_vessel_type(
            db, vessel_type_id, requirement
        )
        if not new_req_data:  # Powinno rzucić wyjątek w CRUD, ale jako zabezpieczenie
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not add sensor requirement",
            )
        # Zwróć pełny obiekt odpowiedzi
        return VesselTypeSensorRequirementResponse(
            sensor_class_id=new_req_data["sensor_class_id"],
            required=new_req_data["required"],
            quantity=new_req_data["quantity"],
            sensor_class=SensorClassResponse(
                id=new_req_data["sensor_class_id"],
                name=new_req_data["sensor_class_name"],
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{vessel_type_id}/sensor-requirements/{sensor_class_id}",
    response_model=VesselTypeSensorRequirementResponse,
)
def update_sensor_requirement(
    vessel_type_id: int,
    sensor_class_id: int,
    requirement_update: VesselTypeSensorRequirementUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated_req_data = crud_vessel_type.update_sensor_requirement_for_vessel_type(
            db, vessel_type_id, sensor_class_id, requirement_update
        )
        if not updated_req_data:  # Powinno rzucić wyjątek w CRUD
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sensor requirement not found or no update performed",
            )
        return VesselTypeSensorRequirementResponse(
            sensor_class_id=updated_req_data["sensor_class_id"],
            required=updated_req_data["required"],
            quantity=updated_req_data["quantity"],
            sensor_class=SensorClassResponse(
                id=updated_req_data["sensor_class_id"],
                name=updated_req_data["sensor_class_name"],
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{vessel_type_id}/sensor-requirements/{sensor_class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_sensor_requirement(
    vessel_type_id: int, sensor_class_id: int, db: Session = Depends(get_db)
):
    deleted = crud_vessel_type.remove_sensor_requirement_from_vessel_type(
        db, vessel_type_id, sensor_class_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor requirement not found for this vessel type",
        )
    return None


# Dodatkowy endpoint do pobrania wszystkich dostępnych klas czujników (przydatne dla dropdownu)
@router.get(
    "/available-sensor-classes/", response_model=List[SensorClassResponse]
)  # Zmieniono ścieżkę dla unikalności
def get_all_available_sensor_classes(db: Session = Depends(get_db)):
    # Załóżmy, że masz crud_sensor_class.get_sensor_classes()
    return crud_sensor_class.get_sensor_classes(db, limit=1000)  # Pobierz wszystkie
