# app/crud/fleet.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Tuple
from app.models.models import Fleet, Operator, Vessel  # Importuj modele
from app.schemas.fleet import FleetCreate, FleetUpdate, FleetResponse


def get_fleets_with_vessel_counts(
    db: Session, skip: int = 0, limit: int = 100
) -> List[
    dict
]:  # Zwraca listę słowników gotowych do serializacji lub dalszego przetwarzania
    """
    Pobiera listę flot wraz z liczbą statków dla każdej floty.
    Każda flota jest wzbogacona o klucz 'vessel_count'.
    """
    fleets_orm = (
        db.query(Fleet)
        .options(joinedload(Fleet.operator))  # Ładujemy operatora od razu
        .order_by(Fleet.name)  # Sortowanie dla spójności
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for fleet_orm in fleets_orm:
        vessels_count = (
            db.query(func.count(Vessel.id))
            .filter(
                Vessel.fleet_id == fleet_orm.id
            )  # Liczymy statki dla tej konkretnej floty
            .scalar()
            or 0  # scalar() zwraca pojedynczą wartość lub None, stąd 'or 0'
        )

        # Przygotuj dane do odpowiedzi, możesz użyć schematu Pydantic
        # Tutaj tworzymy słownik, który może być użyty do stworzenia FleetResponse w warstwie API
        fleet_data = FleetResponse.model_validate(
            fleet_orm
        ).model_dump()  # Konwertuj obiekt ORM na słownik Pydantic
        fleet_data["vessel_count"] = vessels_count  # Dodaj policzoną liczbę statków
        results.append(fleet_data)

    return results


def get_fleet(db: Session, fleet_id: int) -> Optional[Fleet]:
    return (
        db.query(Fleet)
        .options(joinedload(Fleet.operator))
        .filter(Fleet.id == fleet_id)
        .first()
    )


def get_fleets(db: Session, skip: int = 0, limit: int = 100) -> List[Fleet]:
    return (
        db.query(Fleet)
        .options(joinedload(Fleet.operator))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_fleet(db: Session, fleet_data: FleetCreate) -> Fleet:
    # Sprawdź, czy operator istnieje (opcjonalne, ale dobra praktyka)
    operator = db.query(Operator).filter(Operator.id == fleet_data.operator_id).first()
    if not operator:
        # Można rzucić wyjątek lub obsłużyć to w API
        raise ValueError(f"Operator with id {fleet_data.operator_id} not found.")

    db_fleet = Fleet(**fleet_data.model_dump())
    db.add(db_fleet)
    db.commit()
    db.refresh(db_fleet)
    # Aby załadować relację operator od razu po utworzeniu (dla response_model)
    db.refresh(db_fleet, attribute_names=["operator"])
    return db_fleet


def update_fleet(
    db: Session, fleet_id: int, fleet_data: FleetUpdate
) -> Optional[Fleet]:
    db_fleet = get_fleet(db, fleet_id)
    if db_fleet:
        update_data = fleet_data.model_dump(exclude_unset=True)

        # Jeśli operator_id jest aktualizowane, sprawdź czy nowy operator istnieje
        if "operator_id" in update_data and update_data["operator_id"] is not None:
            operator = (
                db.query(Operator)
                .filter(Operator.id == update_data["operator_id"])
                .first()
            )
            if not operator:
                raise ValueError(
                    f"Operator with id {update_data['operator_id']} not found for update."
                )

        for key, value in update_data.items():
            setattr(db_fleet, key, value)
        db.commit()
        db.refresh(db_fleet)
        db.refresh(db_fleet, attribute_names=["operator"])  # Odśwież relację
    return db_fleet


def delete_fleet(db: Session, fleet_id: int) -> Tuple[Optional[Fleet], Optional[str]]:
    db_fleet = get_fleet(db, fleet_id)
    if not db_fleet:
        return None, "Fleet not found."

    # Sprawdź, czy flota nie ma przypisanych statków (Vessel.fleet_id)
    # Zakładając, że masz model Vessel z relacją do Fleet
    if db_fleet.vessels:  # Jeśli relacja nazywa się 'vessels'
        return (
            None,
            f"Cannot delete fleet. It is associated with {len(db_fleet.vessels)} vessel(s).",
        )

    try:
        db.delete(db_fleet)
        db.commit()
        return db_fleet, None
    except (
        Exception
    ) as e:  # Np. IntegrityError, jeśli są inne nieprzewidziane zależności
        db.rollback()
        print(f"Error deleting fleet: {e}")
        return (
            None,
            "Could not delete fleet due to a database constraint or unexpected error.",
        )
