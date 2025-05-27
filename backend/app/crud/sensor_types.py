from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import SensorType, SensorClass, Manufacturer
from app.schemas.sensor_type import SensorTypeCreate, SensorTypeUpdate


def get_sensor_type(db: Session, sensor_type_id: int) -> Optional[SensorType]:
    return db.query(SensorType).filter(SensorType.id == sensor_type_id).first()


def get_sensor_types(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sensor_class_ids: Optional[List[int]] = None,
) -> List[SensorType]:
    query = db.query(SensorType)

    if sensor_class_ids:
        # Filtrujemy tylko jeśli lista sensor_class_ids nie jest pusta
        # i zawiera poprawne ID
        query = query.filter(SensorType.sensor_class_id.in_(sensor_class_ids))

    return query.order_by(SensorType.name).offset(skip).limit(limit).all()


def create_sensor_type(db: Session, sensor_type: SensorTypeCreate) -> SensorType:
    # Walidacja istnienia SensorClass
    db_sensor_class = (
        db.query(SensorClass)
        .filter(SensorClass.id == sensor_type.sensor_class_id)
        .first()
    )
    if not db_sensor_class:
        raise ValueError(
            f"SensorClass with id {sensor_type.sensor_class_id} not found."
        )

    # Walidacja istnienia Manufacturer (jeśli podano)
    if sensor_type.manufacturer_id is not None:
        db_manufacturer = (
            db.query(Manufacturer)
            .filter(Manufacturer.id == sensor_type.manufacturer_id)
            .first()
        )
        if not db_manufacturer:
            raise ValueError(
                f"Manufacturer with id {sensor_type.manufacturer_id} not found."
            )

    db_sensor_type = SensorType(**sensor_type.model_dump())
    db.add(db_sensor_type)
    db.commit()
    db.refresh(db_sensor_type)
    return db_sensor_type


def update_sensor_type(
    db: Session, sensor_type_id: int, sensor_type_update: SensorTypeUpdate
) -> Optional[SensorType]:
    db_sensor_type = get_sensor_type(db, sensor_type_id)
    if not db_sensor_type:
        return None

    update_data = sensor_type_update.model_dump(exclude_unset=True)

    # Walidacja istnienia SensorClass, jeśli jest aktualizowana
    if "sensor_class_id" in update_data and update_data["sensor_class_id"] is not None:
        db_sensor_class = (
            db.query(SensorClass)
            .filter(SensorClass.id == update_data["sensor_class_id"])
            .first()
        )
        if not db_sensor_class:
            raise ValueError(
                f"SensorClass with id {update_data['sensor_class_id']} not found for update."
            )

    # Walidacja istnienia Manufacturer, jeśli jest aktualizowany
    if "manufacturer_id" in update_data:  # Obsługuje też ustawienie na None
        if update_data["manufacturer_id"] is not None:
            db_manufacturer = (
                db.query(Manufacturer)
                .filter(Manufacturer.id == update_data["manufacturer_id"])
                .first()
            )
            if not db_manufacturer:
                raise ValueError(
                    f"Manufacturer with id {update_data['manufacturer_id']} not found for update."
                )
        # Jeśli update_data["manufacturer_id"] to None, to jest to dozwolone (usuwanie powiązania)

    for key, value in update_data.items():
        setattr(db_sensor_type, key, value)

    db.commit()
    db.refresh(db_sensor_type)
    return db_sensor_type


def delete_sensor_type(db: Session, sensor_type_id: int) -> Optional[SensorType]:
    db_sensor_type = get_sensor_type(db, sensor_type_id)
    if db_sensor_type:
        try:
            # Sprawdzenie, czy istnieją powiązane czujniki (Sensors)
            # Model Sensor ma ForeignKey do sensor_types.id z ondelete="RESTRICT",
            # więc baza danych i tak by na to nie pozwoliła, ale lepiej
            # dać bardziej czytelny komunikat.
            if (
                db_sensor_type.sensors
            ):  # Zakładając, że relacja 'sensors' istnieje w modelu SensorType
                raise ValueError(
                    f"Cannot delete sensor type '{db_sensor_type.name}'. It is currently used by one or more sensors."
                )  # [niesprawdzone] czy relacja `sensors` jest zdefiniowana w `SensorType`
                # jeśli nie, to zapytanie `db.query(Sensor).filter(Sensor.sensor_type_id == sensor_type_id).first()` byłoby potrzebne.

            db.delete(db_sensor_type)
            db.commit()
            return db_sensor_type
        except ValueError:  # Przechwycenie naszego własnego błędu
            db.rollback()
            raise
        except Exception as e:  # Np. sqlalchemy.exc.IntegrityError z innych powodów
            db.rollback()
            # Logowanie błędu może być przydatne
            # import logging
            # logging.error(f"Error deleting sensor type: {e}", exc_info=True)
            raise ValueError(
                f"Cannot delete sensor type. An unexpected database error occurred. Original error: {str(e)}"
            )
    return None
