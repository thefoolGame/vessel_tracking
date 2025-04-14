from sqlalchemy.orm import Session
from app.models.models import Operator
from app.schemas.operator import OperatorCreate

def create_operator(db: Session, operator: OperatorCreate):
    db_operator = Operator(**operator.dict())
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return db_operator

def get_operator(db: Session, operator_id: int):
    return db.query(Operator).get(operator_id)

def get_operators(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Operator).offset(skip).limit(limit).all()
