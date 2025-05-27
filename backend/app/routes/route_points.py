from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List

from app.core.database import SessionLocal
from app.schemas.route_point import (
    RoutePointCreate,
    RoutePointUpdate,
    RoutePointResponse,
)
from app.crud import route_points as crud_route_point
from app.crud import vessels as crud_vessel  # Do sprawdzania istnienia statku

router = APIRouter(
    prefix="/vessels/{vessel_id}/route-points",
    tags=["Vessel Route Points"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Funkcja pomocnicza do weryfikacji istnienia statku (można ją przenieść do modułu utils, jeśli używana w wielu miejscach)
def check_vessel_exists(db: Session, vessel_id: int):
    db_vessel = crud_vessel.get_vessel(db, vessel_id=vessel_id)
    if not db_vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with id {vessel_id} not found.",
        )
    return db_vessel


@router.post(
    "/",
    response_model=RoutePointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new route point for a specific vessel",
)
def create_route_point(
    vessel_id: int,  # Pobierane z prefiksu routera
    route_point_in: RoutePointCreate,
    db: Session = Depends(get_db),
):
    try:
        return crud_route_point.create_route_point_for_vessel(
            db=db, route_point_in=route_point_in, vessel_id=vessel_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/",
    response_model=List[RoutePointResponse],
    summary="List all route points for a specific vessel",
)
def list_route_points_for_vessel(
    vessel_id: int,  # Pobierane z prefiksu routera
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    check_vessel_exists(db, vessel_id)
    route_points = crud_route_point.get_route_points_for_vessel(
        db=db, vessel_id=vessel_id, skip=skip, limit=limit
    )
    return route_points


@router.get(
    "/{route_point_id}",
    response_model=RoutePointResponse,
    summary="Get a specific route point by its ID for a specific vessel",
)
def read_route_point(
    vessel_id: int,  # Pobierane z prefiksu routera
    route_point_id: int,
    db: Session = Depends(get_db),
):
    db_route_point = crud_route_point.get_route_point(
        db=db, route_point_id=route_point_id, vessel_id=vessel_id
    )
    if db_route_point is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RoutePoint with id {route_point_id} not found on vessel {vessel_id}.",
        )
    return db_route_point


@router.put(
    "/{route_point_id}",
    response_model=RoutePointResponse,
    summary="Update a route point for a specific vessel",
)
def update_existing_route_point(
    vessel_id: int,  # Pobierane z prefiksu routera
    route_point_id: int,
    route_point_in: RoutePointUpdate,
    db: Session = Depends(get_db),
):
    try:
        updated_route_point = crud_route_point.update_route_point(
            db=db,
            route_point_id=route_point_id,
            route_point_in=route_point_in,
            vessel_id=vessel_id,
        )
        if updated_route_point is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RoutePoint with id {route_point_id} not found on vessel {vessel_id} for update.",
            )
        return updated_route_point
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{route_point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a route point from a specific vessel",
)
def delete_existing_route_point(
    vessel_id: int,  # Pobierane z prefiksu routera
    route_point_id: int,
    db: Session = Depends(get_db),
):
    try:
        deleted_route_point = crud_route_point.delete_route_point(
            db=db, route_point_id=route_point_id, vessel_id=vessel_id
        )
        if deleted_route_point is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RoutePoint with id {route_point_id} not found on vessel {vessel_id} for deletion.",
            )
    except ValueError as e:  # Błędy z CRUD (np. nie można usunąć)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    return None  # Dla statusu 204 No Content


@router.post(
    "/reorder",  # Ścieżka będzie /vessels/{vessel_id}/route-points/reorder
    response_model=List[RoutePointResponse],  # Zwracamy zaktualizowaną listę punktów
    summary="Reorder route points for a specific vessel",
)
def reorder_route_points(
    vessel_id: int,  # Pobierane z prefiksu routera nadrzędnego
    ordered_ids: List[int] = Body(
        ...,
        embed=False,
        description="A list of route_point_ids in the new desired order.",
    ),
    db: Session = Depends(get_db),
):
    # check_vessel_exists(db, vessel_id) # Jest już w CRUD
    try:
        updated_route_points = crud_route_point.update_route_points_order_for_vessel(
            db=db, vessel_id=vessel_id, ordered_route_point_ids=ordered_ids
        )
        return updated_route_points
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
