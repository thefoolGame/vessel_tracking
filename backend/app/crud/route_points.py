from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.models.models import RoutePoint, Vessel
from app.schemas.route_point import RoutePointCreate, RoutePointUpdate
from sqlalchemy import func  # Dla WKT


def get_route_point(
    db: Session, route_point_id: int, vessel_id: Optional[int] = None
) -> Optional[RoutePoint]:
    query = db.query(RoutePoint).filter(RoutePoint.route_point_id == route_point_id)
    if vessel_id is not None:
        query = query.filter(RoutePoint.vessel_id == vessel_id)
    return query.first()


def get_route_points_for_vessel(
    db: Session, vessel_id: int, skip: int = 0, limit: int = 100
) -> List[RoutePoint]:
    # Sprawdź, czy statek istnieje
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        return []

    return (
        db.query(RoutePoint)
        .filter(RoutePoint.vessel_id == vessel_id)
        .order_by(RoutePoint.sequence_number)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_route_point_for_vessel(
    db: Session, route_point_in: RoutePointCreate, vessel_id: int
) -> RoutePoint:
    # Sprawdź, czy statek istnieje
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        raise ValueError(f"Vessel with id {vessel_id} not found.")

    db_route_point = RoutePoint(
        **route_point_in.model_dump(
            exclude={"planned_position"}
        ),  # Wykluczamy string WKT
        vessel_id=vessel_id,
        # Bezpośrednie przypisanie stringu WKT do pola Geometry
        # SQLAlchemy/GeoAlchemy2 powinno to obsłużyć.
        planned_position=route_point_in.planned_position,
    )

    try:
        db.add(db_route_point)
        db.commit()
        db.refresh(db_route_point)
        return db_route_point
    except IntegrityError as e:
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        if (
            "uix_vessel_sequence" in error_detail.lower()
        ):  # Sprawdzenie nazwy ograniczenia
            raise ValueError(
                f"Route point with sequence number {route_point_in.sequence_number} "
                f"already exists for vessel {vessel_id}."
            )
        raise ValueError(f"Database integrity error: {error_detail}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred: {str(e)}")


def update_route_point(
    db: Session,
    route_point_id: int,
    route_point_in: RoutePointUpdate,
    vessel_id: int,
) -> Optional[RoutePoint]:
    db_route_point = get_route_point(
        db, route_point_id=route_point_id, vessel_id=vessel_id
    )
    if not db_route_point:
        return None

    update_data = route_point_in.model_dump(exclude_unset=True)

    if "planned_position" in update_data and update_data["planned_position"]:
        db_route_point.planned_position = update_data.pop("planned_position")

    for key, value in update_data.items():
        setattr(db_route_point, key, value)

    try:
        db.commit()
        db.refresh(db_route_point)
        return db_route_point
    except IntegrityError as e:
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        if (
            "uix_vessel_sequence" in error_detail.lower()
            and "sequence_number" in update_data
        ):
            raise ValueError(
                f"Route point with sequence number {update_data['sequence_number']} "
                f"already exists for vessel {vessel_id}."
            )
        raise ValueError(f"Database integrity error during update: {error_detail}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during update: {str(e)}")


def delete_route_point(
    db: Session, route_point_id: int, vessel_id: int
) -> Optional[RoutePoint]:
    db_route_point = get_route_point(
        db, route_point_id=route_point_id, vessel_id=vessel_id
    )
    if not db_route_point:
        return None

    try:
        db.delete(db_route_point)
        db.commit()
        return db_route_point
    except IntegrityError as e:  # Na wypadek nieprzewidzianych ograniczeń FK
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        raise ValueError(f"Cannot delete route point. Database error: {error_detail}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during deletion: {str(e)}")


def update_route_points_order_for_vessel(
    db: Session, vessel_id: int, ordered_route_point_ids: List[int]
) -> List[RoutePoint]:
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        raise ValueError(f"Vessel with id {vessel_id} not found.")

    # Pobierz punkty trasy, które są częścią operacji reorder
    # i należą do danego statku.
    # Ważne jest, aby operować tylko na tych punktach, które faktycznie są w ordered_route_point_ids.
    route_points_to_reorder = (
        db.query(RoutePoint)
        .filter(RoutePoint.vessel_id == vessel_id)
        .filter(RoutePoint.route_point_id.in_(ordered_route_point_ids))
        .all()
    )

    # Stwórz mapę dla łatwego dostępu ID -> obiekt
    route_points_map = {rp.route_point_id: rp for rp in route_points_to_reorder}

    # Sprawdź, czy wszystkie ID z listy istnieją i zostały pobrane
    if len(route_points_map) != len(
        set(ordered_route_point_ids)
    ):  # Użyj set dla unikalnych ID z listy
        missing_or_mismatched_ids = set(ordered_route_point_ids) - set(
            route_points_map.keys()
        )
        if missing_or_mismatched_ids:
            raise ValueError(
                f"Route points with IDs {missing_or_mismatched_ids} not found or do not belong to vessel {vessel_id}."
            )
        # Ten przypadek jest mało prawdopodobny, jeśli powyższe jest prawdą
        raise ValueError(
            "Mismatch in provided route point IDs and existing route points for the vessel."
        )

    # Sprawdź, czy liczba unikalnych ID w ordered_route_point_ids zgadza się z liczbą pobranych punktów
    # To zapobiega problemom, jeśli ordered_route_point_ids zawiera duplikaty.
    if len(set(ordered_route_point_ids)) != len(route_points_to_reorder):
        raise ValueError(
            "Duplicate IDs found in the ordered list or mismatch with existing points."
        )

    try:
        for i, route_point_id in enumerate(ordered_route_point_ids):
            route_point = route_points_map.get(route_point_id)
            if route_point:
                route_point.sequence_number = -(i + 1)
                db.add(route_point)

        db.flush()

        updated_route_points_final = []
        for index, route_point_id in enumerate(ordered_route_point_ids):
            route_point = route_points_map.get(route_point_id)
            if route_point:  # Powinien istnieć
                route_point.sequence_number = (
                    index + 1
                )  # Nowy, właściwy numer sekwencyjny
                db.add(route_point)
                updated_route_points_final.append(route_point)

        db.commit()  # Commit obu faz naraz

        for rp in updated_route_points_final:
            db.refresh(rp)

        return sorted(updated_route_points_final, key=lambda rp: rp.sequence_number)

    except IntegrityError as e:
        db.rollback()
        # Ten błąd nie powinien już wystąpić z powodu "uix_vessel_sequence", jeśli logika jest poprawna.
        # Może wystąpić z innych powodów.
        raise ValueError(f"Database integrity error during reorder: {str(e.orig)}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during reorder: {str(e)}")
