from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from sqlalchemy.exc import IntegrityError
from app.models.models import (
    SensorClass,
    SensorType,
    vessel_type_required_sensor_types as vt_req_table,
)
from app.schemas.sensor_class import SensorClassCreate, SensorClassUpdate


def get_sensor_class(db: Session, sensor_class_id: int) -> Optional[SensorClass]:
    return db.query(SensorClass).filter(SensorClass.id == sensor_class_id).first()


def get_sensor_class_by_name(db: Session, name: str) -> Optional[SensorClass]:
    return db.query(SensorClass).filter(SensorClass.name == name).first()


def get_sensor_classes(
    db: Session, skip: int = 0, limit: int = 100
) -> List[SensorClass]:
    return (
        db.query(SensorClass).order_by(SensorClass.name).offset(skip).limit(limit).all()
    )


def create_sensor_class(
    db: Session, sensor_class: SensorClassCreate
) -> Tuple[Optional[SensorClass], Optional[str]]:
    """
    Tworzy nową klasę czujnika.
    Zwraca (SensorClass | None, error_message | None)
    """
    if get_sensor_class_by_name(db, name=sensor_class.name):
        return None, f"Sensor class with name '{sensor_class.name}' already exists."

    db_sensor_class = SensorClass(**sensor_class.model_dump())
    try:
        db.add(db_sensor_class)
        db.commit()
        db.refresh(db_sensor_class)
        return db_sensor_class, None
    except (
        IntegrityError
    ):  # Na wypadek, gdyby unikalność nazwy była też na poziomie bazy
        db.rollback()
        return (
            None,
            f"Sensor class with name '{sensor_class.name}' already exists (database constraint).",
        )
    except Exception as e:
        db.rollback()
        return None, f"An unexpected error occurred: {str(e)}"


def update_sensor_class(
    db: Session, sensor_class_id: int, sensor_class_update: SensorClassUpdate
) -> Tuple[Optional[SensorClass], Optional[str]]:
    """
    Aktualizuje istniejącą klasę czujnika.
    Zwraca (SensorClass | None, error_message | None)
    """
    db_sensor_class = get_sensor_class(db, sensor_class_id)
    if not db_sensor_class:
        return None, "Sensor class not found."

    update_data = sensor_class_update.model_dump(exclude_unset=True)

    if not update_data:
        return db_sensor_class, "No data provided for update."  # Lub None, "No data..."

    if "name" in update_data and update_data["name"] != db_sensor_class.name:
        if get_sensor_class_by_name(db, name=update_data["name"]):
            return (
                None,
                f"Sensor class with name '{update_data['name']}' already exists.",
            )

    for key, value in update_data.items():
        setattr(db_sensor_class, key, value)

    try:
        db.commit()
        db.refresh(db_sensor_class)
        return db_sensor_class, None
    except IntegrityError:
        db.rollback()
        return None, "Sensor class name conflict during update (database constraint)."
    except Exception as e:
        db.rollback()
        return None, f"An unexpected error occurred during update: {str(e)}"


def delete_sensor_class(
    db: Session, sensor_class_id: int
) -> Tuple[Optional[SensorClass], Optional[str]]:
    """
    Usuwa klasę czujnika, jeśli nie jest używana.
    Zwraca (SensorClass | None, error_message | None)
    """
    db_sensor_class = get_sensor_class(db, sensor_class_id)
    if not db_sensor_class:
        return None, "Sensor class not found."

    # Sprawdź użycie w SensorType
    related_sensor_types_count = (
        db.query(SensorType)
        .filter(SensorType.sensor_class_id == sensor_class_id)
        .count()
    )
    if related_sensor_types_count > 0:
        return (
            None,
            f"Cannot delete sensor class. It is associated with {related_sensor_types_count} sensor type(s).",
        )

    # Sprawdź użycie w vessel_type_required_sensor_types
    # Używamy vt_req_table zdefiniowanego w models.py
    related_vessel_requirements_count = (
        db.query(vt_req_table)
        .filter(vt_req_table.c.sensor_class_id == sensor_class_id)
        .count()
    )
    if related_vessel_requirements_count > 0:
        return (
            None,
            f"Cannot delete sensor class. It is a requirement for {related_vessel_requirements_count} vessel type(s).",
        )

    try:
        deleted_sensor_class_name = (
            db_sensor_class.name
        )  # Zachowaj nazwę na potrzeby komunikatu
        db.delete(db_sensor_class)
        db.commit()
        # Zwracamy słownik z informacją, bo obiekt już nie istnieje w sesji po usunięciu
        return {"id": sensor_class_id, "name": deleted_sensor_class_name}, None
    except IntegrityError as e:  # Dodatkowe zabezpieczenie
        db.rollback()
        return (
            None,
            f"Could not delete sensor class due to a database integrity constraint: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        return None, f"An unexpected error occurred during deletion: {str(e)}"
