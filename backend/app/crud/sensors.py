from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.models.models import Sensor, Vessel, SensorType
from app.schemas.sensor import SensorCreate, SensorUpdate


def get_sensor(
    db: Session, sensor_id: int, vessel_id: Optional[int] = None
) -> Optional[Sensor]:
    query = db.query(Sensor).filter(Sensor.id == sensor_id)
    if vessel_id is not None:
        query = query.filter(Sensor.vessel_id == vessel_id)
    return query.first()


def get_sensors_for_vessel(
    db: Session, vessel_id: int, skip: int = 0, limit: int = 100
) -> List[Sensor]:
    return (
        db.query(Sensor)
        .filter(Sensor.vessel_id == vessel_id)
        .order_by(Sensor.name)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_sensor_for_vessel(
    db: Session, sensor_in: SensorCreate, vessel_id: int
) -> Sensor:
    """Tworzy nowy sensor dla określonego statku."""
    # 1. Sprawdź, czy statek istnieje
    db_vessel = db.query(Vessel).filter(Vessel.id == vessel_id).first()
    if not db_vessel:
        raise ValueError(f"Vessel with id {vessel_id} not found.")

    # 2. Sprawdź, czy typ sensora istnieje
    db_sensor_type = (
        db.query(SensorType).filter(SensorType.id == sensor_in.sensor_type_id).first()
    )
    if not db_sensor_type:
        raise ValueError(f"SensorType with id {sensor_in.sensor_type_id} not found.")

    # 3. Utwórz obiekt Sensor
    # Walidator @validates("sensor_type_id") w modelu Sensor powinien zostać
    # automatycznie wywołany przez SQLAlchemy podczas przypisywania wartości.
    # Ten walidator sprawdza, czy klasa czujnika jest dozwolona dla typu statku.
    db_sensor = Sensor(**sensor_in.model_dump(), vessel_id=vessel_id)

    try:
        db.add(db_sensor)
        db.commit()
        db.refresh(db_sensor)
        return db_sensor
    except IntegrityError as e:
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        raise ValueError(f"Database integrity error: {error_detail}")
    except ValueError as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred: {str(e)}")


def update_sensor(
    db: Session,
    sensor_id: int,
    sensor_in: SensorUpdate,
    vessel_id: int,
) -> Optional[Sensor]:
    db_sensor = get_sensor(db, sensor_id=sensor_id, vessel_id=vessel_id)
    if not db_sensor:
        return None

    update_data = sensor_in.model_dump(exclude_unset=True)

    # Jeśli sensor_type_id jest aktualizowany, sprawdź czy nowy typ istnieje
    if "sensor_type_id" in update_data:
        new_sensor_type_id = update_data["sensor_type_id"]
        db_sensor_type = (
            db.query(SensorType).filter(SensorType.id == new_sensor_type_id).first()
        )
        if not db_sensor_type:
            raise ValueError(
                f"SensorType with id {new_sensor_type_id} not found for update."
            )
        # Walidator @validates("sensor_type_id") w modelu Sensor
        # zostanie wywołany przy setattr.

    for key, value in update_data.items():
        setattr(db_sensor, key, value)

    try:
        db.commit()
        db.refresh(db_sensor)
        return db_sensor
    except IntegrityError as e:
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        raise ValueError(f"Database integrity error during update: {error_detail}")
    except ValueError as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during update: {str(e)}")


def delete_sensor(db: Session, sensor_id: int, vessel_id: int) -> Optional[Sensor]:
    """Usuwa sensor ze statku."""
    db_sensor = get_sensor(db, sensor_id=sensor_id, vessel_id=vessel_id)
    if not db_sensor:
        return None

    try:
        # Sprawdzenie, czy sensor nie jest powiązany z Alertami lub Odczytami,
        # jeśli ondelete="SET NULL" lub "RESTRICT" jest ustawione w tych modelach.
        # Model SensorReading ma ondelete="CASCADE" dla sensor_id.
        # Model Alert ma ondelete="SET NULL" dla sensor_id.
        # Usunięcie sensora spowoduje ustawienie sensor_id na NULL w powiązanych alertach.
        db.delete(db_sensor)
        db.commit()
        return db_sensor
    except IntegrityError as e:  # Np. jeśli jakaś inna tabela miałaby RESTRICT
        db.rollback()
        orig_error = getattr(e, "orig", None)
        error_detail = str(orig_error) if orig_error else str(e)
        raise ValueError(
            f"Cannot delete sensor. It might be referenced by other records. Details: {error_detail}"
        )
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"An unexpected error occurred during deletion: {str(e)}")
