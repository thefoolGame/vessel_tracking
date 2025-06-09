from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.operator import OperatorCreate, OperatorUpdate, OperatorResponse
from app.crud import operator as crud_operator

router = APIRouter(prefix="/operators", tags=["Operators"])


@router.post("/", response_model=OperatorResponse, status_code=status.HTTP_201_CREATED)
def create_new_operator(
    operator_data: OperatorCreate,  # Zmieniono nazwę parametru
    db: Session = Depends(get_db),
):
    db_operator = crud_operator.create_operator(db=db, operator=operator_data)
    # Aby zwrócić OperatorResponse z poprawnymi (zerowymi) liczbami:
    return crud_operator.get_operator_with_counts(db, db_operator.id)


@router.get(
    "/", response_model=List[OperatorResponse]
)  # Zmieniono response_model na listę słowników
def read_operators_with_counts(  # Zmieniono nazwę funkcji
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    operators = crud_operator.get_operators_with_counts(db, skip=skip, limit=limit)
    # Funkcja CRUD już zwraca listę słowników pasujących do OperatorResponse
    return operators


@router.get(
    "/{operator_id}", response_model=OperatorResponse
)  # Zmieniono response_model na słownik
def read_operator_with_counts(  # Zmieniono nazwę funkcji
    operator_id: int, db: Session = Depends(get_db)
):
    operator_data = crud_operator.get_operator_with_counts(db, operator_id=operator_id)
    if operator_data is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    return operator_data


@router.put("/{operator_id}", response_model=OperatorResponse)
def update_existing_operator(
    operator_id: int,  # Potrzebne, jeśli będziesz obsługiwał JSON w formularzach, na razie nie dla Operatora
    operator_update_data: OperatorUpdate,  # Zmieniono nazwę parametru
    db: Session = Depends(get_db),
):
    db_operator_orm = crud_operator.update_operator(  # Ta funkcja zwraca obiekt ORM
        db=db, operator_id=operator_id, operator_update=operator_update_data
    )
    if db_operator_orm is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    # Pobierz zaktualizowane dane z liczbami
    return crud_operator.get_operator_with_counts(db, db_operator_orm.id)


@router.delete("/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_operator(operator_id: int, db: Session = Depends(get_db)):
    deleted_operator, error_message = crud_operator.delete_operator(
        db, operator_id=operator_id
    )
    if error_message:
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=error_message
            )
    if not deleted_operator and not error_message:
        raise HTTPException(
            status_code=404, detail="Operator not found or could not be processed."
        )
    return None
