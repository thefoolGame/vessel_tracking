from sqlalchemy.orm import Session
from sqlalchemy import func  # Potrzebne do func.count()
from typing import List, Optional, Tuple
from app.models.models import Operator, Fleet, Vessel  # Importuj powiązane modele
from app.schemas.operator import (
    OperatorCreate,
    OperatorUpdate,
    OperatorResponse,
)


def get_operator_with_counts(db: Session, operator_id: int) -> Optional[dict]:
    """Pobiera operatora wraz z liczbą flot i statków."""
    db_operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not db_operator:
        return None

    fleets_count = (
        db.query(func.count(Fleet.id)).filter(Fleet.operator_id == operator_id).scalar()
        or 0
    )
    vessels_count = (
        db.query(func.count(Vessel.id))
        .filter(Vessel.operator_id == operator_id)
        .scalar()
        or 0
    )

    operator_data = OperatorResponse.model_validate(db_operator).model_dump()
    operator_data["fleets_count"] = fleets_count
    operator_data["vessels_count"] = vessels_count

    return operator_data


def get_operators_with_counts(
    db: Session, skip: int = 0, limit: int = 100
) -> List[dict]:
    """Pobiera listę operatorów wraz z liczbą flot i statków dla każdego."""
    operators_orm = (
        db.query(Operator).order_by(Operator.name).offset(skip).limit(limit).all()
    )

    results = []
    for op_orm in operators_orm:
        fleets_count = (
            db.query(func.count(Fleet.id))
            .filter(Fleet.operator_id == op_orm.id)
            .scalar()
            or 0
        )
        # Można by też użyć len(op_orm.fleets), ale to załaduje wszystkie obiekty flot, co może być nieefektywne.
        # Lepsze jest osobne zapytanie count.

        vessels_count = (
            db.query(func.count(Vessel.id))
            .filter(Vessel.operator_id == op_orm.id)
            .scalar()
            or 0
        )
        # Podobnie, len(op_orm.vessels) załaduje wszystkie statki.

        operator_data = OperatorResponse.model_validate(op_orm).model_dump()
        operator_data["fleets_count"] = fleets_count
        operator_data["vessels_count"] = vessels_count
        results.append(operator_data)

    return results


# Funkcja tworzenia pozostaje prosta, bo liczby flot/statków będą 0 dla nowego operatora
def create_operator(
    db: Session, operator: OperatorCreate
) -> Operator:  # Zwraca obiekt ORM
    db_operator = Operator(**operator.model_dump())
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return db_operator  # Endpoint API przekształci to na OperatorResponse (z count=0)


# Funkcja aktualizacji - aktualizuje tylko pola operatora, liczby są pochodne
def update_operator(
    db: Session, operator_id: int, operator_update: OperatorUpdate
) -> Optional[Operator]:  # Zwraca obiekt ORM
    db_operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if db_operator:
        update_data = operator_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_operator, key, value)
        db.commit()
        db.refresh(db_operator)
    return db_operator  # Endpoint API przekształci to na OperatorResponse z aktualnymi liczbami


# Funkcja usuwania - z obsługą zależności
def delete_operator(
    db: Session, operator_id: int
) -> Tuple[Optional[Operator], Optional[str]]:
    db_operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not db_operator:
        return None, "Operator not found."

    # Sprawdź powiązane Floty
    # ondelete="RESTRICT" w Fleet.operator_id
    related_fleets_count = (
        db.query(Fleet).filter(Fleet.operator_id == operator_id).count()
    )
    if related_fleets_count > 0:
        return (
            None,
            f"Cannot delete operator. It is associated with {related_fleets_count} fleet(s).",
        )

    # Sprawdź powiązane Statki
    # ondelete="RESTRICT" w Vessel.operator_id
    related_vessels_count = (
        db.query(Vessel).filter(Vessel.operator_id == operator_id).count()
    )
    if related_vessels_count > 0:
        return (
            None,
            f"Cannot delete operator. It is associated with {related_vessels_count} vessel(s).",
        )

    # Sprawdź powiązane Alerty (acknowledged_by)
    # ondelete="SET NULL" w Alert.acknowledged_by - to nie blokuje usunięcia, ale warto wiedzieć
    # related_alerts_count = db.query(Alert).filter(Alert.acknowledged_by == operator_id).count()
    # if related_alerts_count > 0:
    #     print(f"Operator {operator_id} acknowledged {related_alerts_count} alerts. These will be set to NULL.")

    try:
        db.delete(db_operator)
        db.commit()
        return db_operator, None
    except Exception as e:  # Np. IntegrityError, jeśli inne nieprzewidziane zależności
        db.rollback()
        print(f"Error deleting operator: {e}")
        return (
            None,
            "Could not delete operator due to a database constraint or unexpected error.",
        )
