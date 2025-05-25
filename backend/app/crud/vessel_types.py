from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import (
    select,
    delete,
    update,
)  # Dla operacji na tabeli asocjacyjnej
from typing import List, Optional, Dict, Any, Tuple
from app.models.models import (
    Vessel,
    VesselType,
    Manufacturer,
    SensorClass,
    vessel_type_required_sensor_types as vt_req_table,
)
from app.schemas.vessel_type import (
    VesselTypeCreate,
    VesselTypeUpdate,
    VesselTypeSensorRequirementCreate,
    VesselTypeSensorRequirementUpdate,
)


def get_vessel_type(db: Session, vessel_type_id: int) -> Optional[VesselType]:
    return db.query(VesselType).filter(VesselType.id == vessel_type_id).first()


def get_vessel_types(db: Session, skip: int = 0, limit: int = 100) -> List[VesselType]:
    return db.query(VesselType).offset(skip).limit(limit).all()


def create_vessel_type(db: Session, vessel_type: VesselTypeCreate) -> VesselType:
    # Sprawdź, czy producent istnieje
    manufacturer = (
        db.query(Manufacturer)
        .filter(Manufacturer.id == vessel_type.manufacturer_id)
        .first()
    )
    if not manufacturer:
        # Można rzucić wyjątek lub obsłużyć to w warstwie API
        raise ValueError(
            f"Manufacturer with id {vessel_type.manufacturer_id} not found"
        )

    db_vessel_type = VesselType(**vessel_type.model_dump())
    db.add(db_vessel_type)
    db.commit()
    db.refresh(db_vessel_type)
    return db_vessel_type


def update_vessel_type(
    db: Session, vessel_type_id: int, vessel_type_update: VesselTypeUpdate
) -> Optional[VesselType]:
    db_vessel_type = get_vessel_type(db, vessel_type_id)
    if db_vessel_type:
        update_data = vessel_type_update.model_dump(exclude_unset=True)

        # Sprawdź, czy producent istnieje, jeśli jest aktualizowany
        if "manufacturer_id" in update_data:
            manufacturer = (
                db.query(Manufacturer)
                .filter(Manufacturer.id == update_data["manufacturer_id"])
                .first()
            )
            if not manufacturer:
                raise ValueError(
                    f"Manufacturer with id {update_data['manufacturer_id']} not found for update"
                )

        for key, value in update_data.items():
            setattr(db_vessel_type, key, value)
        db.commit()
        db.refresh(db_vessel_type)
    return db_vessel_type


def delete_vessel_type(
    db: Session, vessel_type_id: int
) -> Tuple[Optional[VesselType], Optional[str]]:
    """
    Usuwa typ statku, jeśli nie ma powiązanych statków.
    Zwraca krotkę: (usunięty_obiekt | None, komunikat_błędu | None)
    """
    db_vessel_type = get_vessel_type(db, vessel_type_id)  # Zakładam, że masz tę funkcję
    if not db_vessel_type:
        return None, "Vessel Type not found."

    # Sprawdź powiązane statki (Vessel)
    related_vessels_count = (
        db.query(Vessel).filter(Vessel.vessel_type_id == vessel_type_id).count()
    )
    if related_vessels_count > 0:
        return (
            None,
            f"Cannot delete vessel type. It is associated with {related_vessels_count} vessel(s).",
        )

    # Sprawdź powiązania z vessel_type_required_sensor_types (jeśli nie ma kaskadowego usuwania)
    # Jeśli relacja VesselType.required_sensor_classes ma cascade="all, delete" lub "all, delete-orphan",
    # SQLAlchemy powinno samo usunąć wpisy z tabeli asocjacyjnej.
    # W przeciwnym razie, musisz je usunąć ręcznie:
    # db.execute(vt_req_table.delete().where(vt_req_table.c.vessel_type_id == vessel_type_id))

    try:
        db.delete(db_vessel_type)
        db.commit()
        return db_vessel_type, None  # Sukces
    except IntegrityError as e:  # Ogólny błąd integralności jako fallback
        db.rollback()
        print(f"IntegrityError during vessel type deletion: {e}")
        # Spróbuj wyciągnąć bardziej szczegółowy komunikat z błędu psycopg2, jeśli to możliwe
        # orig_error = getattr(e, 'orig', None)
        # if orig_error and hasattr(orig_error, 'pgerror'):
        #     pg_error_msg = orig_error.pgerror
        #     if pg_error_msg:
        #         return None, f"Database integrity error: {pg_error_msg}"
        return (
            None,
            "Could not delete vessel type due to a database integrity constraint.",
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error during vessel type deletion: {e}")
        return None, "An unexpected error occurred during deletion."


# --- Funkcje CRUD dla wymagań czujników ---


def get_sensor_requirements_for_vessel_type(
    db: Session, vessel_type_id: int
) -> List[Dict[str, Any]]:
    """Zwraca listę wymagań czujników dla danego typu statku, wraz z danymi SensorClass."""
    stmt = (
        select(
            vt_req_table.c.sensor_class_id,
            vt_req_table.c.required,
            vt_req_table.c.quantity,
            SensorClass.name.label("sensor_class_name"),
            SensorClass.description.label("sensor_class_description"),
        )
        .join(SensorClass, vt_req_table.c.sensor_class_id == SensorClass.id)
        .where(vt_req_table.c.vessel_type_id == vessel_type_id)
        .order_by(SensorClass.name)
    )
    results = (
        db.execute(stmt).mappings().all()
    )  # Zwraca listę obiektów podobnych do słowników
    return results


def add_sensor_requirement_to_vessel_type(
    db: Session, vessel_type_id: int, requirement: VesselTypeSensorRequirementCreate
) -> Optional[Dict[str, Any]]:
    # Sprawdź, czy VesselType i SensorClass istnieją
    vessel_type = db.query(VesselType).filter(VesselType.id == vessel_type_id).first()
    if not vessel_type:
        raise ValueError(f"VesselType with id {vessel_type_id} not found.")
    sensor_class = (
        db.query(SensorClass)
        .filter(SensorClass.id == requirement.sensor_class_id)
        .first()
    )
    if not sensor_class:
        raise ValueError(
            f"SensorClass with id {requirement.sensor_class_id} not found."
        )

    # Sprawdź, czy powiązanie już istnieje
    existing_req = db.execute(
        select(vt_req_table).where(
            (vt_req_table.c.vessel_type_id == vessel_type_id)
            & (vt_req_table.c.sensor_class_id == requirement.sensor_class_id)
        )
    ).first()
    if existing_req:
        raise ValueError(
            "This sensor class requirement already exists for this vessel type."
        )

    stmt = vt_req_table.insert().values(
        vessel_type_id=vessel_type_id,
        sensor_class_id=requirement.sensor_class_id,
        required=requirement.required,
        quantity=requirement.quantity,
    )
    db.execute(stmt)
    db.commit()
    # Zwróć nowo utworzone powiązanie (można by je pobrać ponownie dla pełnych danych)
    return {
        "vessel_type_id": vessel_type_id,
        "sensor_class_id": requirement.sensor_class_id,
        "sensor_class_name": sensor_class.name,  # Dodajemy dla wygody
        "required": requirement.required,
        "quantity": requirement.quantity,
    }


def update_sensor_requirement_for_vessel_type(
    db: Session,
    vessel_type_id: int,
    sensor_class_id: int,
    requirement_update: VesselTypeSensorRequirementUpdate,
) -> Optional[Dict[str, Any]]:
    # Sprawdź, czy powiązanie istnieje
    existing_req = db.execute(
        select(
            vt_req_table.c.required, vt_req_table.c.quantity
        ).where(  # Pobierz obecne wartości
            (vt_req_table.c.vessel_type_id == vessel_type_id)
            & (vt_req_table.c.sensor_class_id == sensor_class_id)
        )
    ).first()
    if not existing_req:
        raise ValueError("Sensor class requirement not found for this vessel type.")

    update_values = requirement_update.model_dump(exclude_unset=True)
    if not update_values:  # Nic do aktualizacji
        # Zwróć istniejące dane
        sensor_class = (
            db.query(SensorClass).filter(SensorClass.id == sensor_class_id).first()
        )
        return {
            "vessel_type_id": vessel_type_id,
            "sensor_class_id": sensor_class_id,
            "sensor_class_name": sensor_class.name if sensor_class else "Unknown",
            "required": existing_req.required,
            "quantity": existing_req.quantity,
        }

    stmt = (
        update(vt_req_table)
        .where(
            (vt_req_table.c.vessel_type_id == vessel_type_id)
            & (vt_req_table.c.sensor_class_id == sensor_class_id)
        )
        .values(**update_values)
    )
    db.execute(stmt)
    db.commit()
    # Zwróć zaktualizowane powiązanie
    sensor_class = (
        db.query(SensorClass).filter(SensorClass.id == sensor_class_id).first()
    )
    updated_req = db.execute(
        select(vt_req_table.c.required, vt_req_table.c.quantity).where(
            (vt_req_table.c.vessel_type_id == vessel_type_id)
            & (vt_req_table.c.sensor_class_id == sensor_class_id)
        )
    ).first()
    return {
        "vessel_type_id": vessel_type_id,
        "sensor_class_id": sensor_class_id,
        "sensor_class_name": sensor_class.name if sensor_class else "Unknown",
        "required": updated_req.required,
        "quantity": updated_req.quantity,
    }


def remove_sensor_requirement_from_vessel_type(
    db: Session, vessel_type_id: int, sensor_class_id: int
) -> bool:
    stmt = delete(vt_req_table).where(
        (vt_req_table.c.vessel_type_id == vessel_type_id)
        & (vt_req_table.c.sensor_class_id == sensor_class_id)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0  # Zwraca True, jeśli usunięto wiersz
