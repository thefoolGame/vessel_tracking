from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.models import Manufacturer, VesselType, SensorType
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerUpdate
from typing import List, Optional, Tuple
from pydantic import HttpUrl


def create_manufacturer(db: Session, manufacturer: ManufacturerCreate) -> Manufacturer:
    create_dict = manufacturer.model_dump()

    # Jawna konwersja HttpUrl na string, jeśli istnieje
    if "website" in create_dict and isinstance(create_dict["website"], HttpUrl):
        create_dict["website"] = str(create_dict["website"])
    elif "website" in create_dict and create_dict["website"] is None:
        create_dict["website"] = None
    if "contact_info" in create_dict and create_dict["contact_info"] is None:
        pass

    db_manufacturer = Manufacturer(**create_dict)
    try:
        db.add(db_manufacturer)
        db.commit()
        db.refresh(db_manufacturer)
    except Exception as e:
        db.rollback()
        print(f"Error during manufacturer create commit: {e}")
        raise
    return db_manufacturer


def get_manufacturer(db: Session, manufacturer_id: int) -> Optional[Manufacturer]:
    return db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()


def get_manufacturers(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Manufacturer]:
    return db.query(Manufacturer).offset(skip).limit(limit).all()


def update_manufacturer(
    db: Session, manufacturer_id: int, manufacturer_update: ManufacturerUpdate
) -> Optional[Manufacturer]:
    db_manufacturer = get_manufacturer(db, manufacturer_id)
    if db_manufacturer:
        # model_dump() bez argumentów powinien też działać dla HttpUrl -> str.
        update_data = manufacturer_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            # Jawna konwersja HttpUrl na string PRZED przypisaniem do modelu SQLAlchemy
            if key == "website" and isinstance(value, HttpUrl):
                setattr(db_manufacturer, key, str(value))
            elif (
                key == "website" and value is None
            ):  # Obsługa ustawienia website na None
                setattr(db_manufacturer, key, None)
            else:
                setattr(db_manufacturer, key, value)
        try:
            db.commit()
            db.refresh(db_manufacturer)
        except Exception as e:
            db.rollback()
            print(f"Error during manufacturer update commit: {e}")  # Loguj błąd
            raise  # Rzuć dalej, aby endpoint API mógł go obsłużyć
    return db_manufacturer


def delete_manufacturer(
    db: Session, manufacturer_id: int
) -> Tuple[Optional[Manufacturer], Optional[str]]:
    """
    Usuwa producenta, jeśli nie ma powiązanych typów statków lub czujników.
    Zwraca krotkę: (usunięty_obiekt | None, komunikat_błędu | None)
    """
    db_manufacturer = get_manufacturer(db, manufacturer_id)
    if not db_manufacturer:
        return None, "Manufacturer not found."

    # Sprawdź powiązane VesselType
    related_vessel_types_count = (
        db.query(VesselType)
        .filter(VesselType.manufacturer_id == manufacturer_id)
        .count()
    )
    if related_vessel_types_count > 0:
        return (
            None,
            f"Cannot delete manufacturer. It is associated with {related_vessel_types_count} vessel type(s).",
        )

    # Sprawdź powiązane SensorType
    related_sensor_types_count = (
        db.query(SensorType)
        .filter(SensorType.manufacturer_id == manufacturer_id)
        .count()
    )
    if related_sensor_types_count > 0:
        return (
            None,
            f"Cannot delete manufacturer. It is associated with {related_sensor_types_count} sensor type(s).",
        )

    try:
        db.delete(db_manufacturer)
        db.commit()
        return db_manufacturer, None  # Sukces, brak błędu
    except IntegrityError as e:
        db.rollback()
        # Ten błąd nie powinien wystąpić, jeśli powyższe sprawdzenia są kompletne
        # i ondelete="RESTRICT" jest ustawione, ale jako dodatkowe zabezpieczenie.
        print(f"IntegrityError during manufacturer deletion: {e}")
        return (
            None,
            "Could not delete manufacturer due to a database integrity constraint (unexpected).",
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error during manufacturer deletion: {e}")
        return None, "An unexpected error occurred during deletion."
