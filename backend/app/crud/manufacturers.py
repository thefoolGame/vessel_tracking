from sqlalchemy.orm import Session
from app.models.models import Manufacturer
from app.schemas.manufacturer import ManufacturerCreate

def create_manufacturer(db: Session, manufacturer: ManufacturerCreate):
    data = manufacturer.dict()

    # jawna konwersja pola website do stringa (jeśli nie jest None)
    if data.get('website'):
        data['website'] = str(data['website'])

    db_manufacturer = Manufacturer(**data)
    db.add(db_manufacturer)
    db.commit()
    db.refresh(db_manufacturer)
    return db_manufacturer

def get_manufacturer(db: Session, manufacturer_id: int):
    return db.query(Manufacturer).get(manufacturer_id)

def get_manufacturers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Manufacturer).offset(skip).limit(limit).all()
