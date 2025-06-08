from fastapi import HTTPException, status, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Annotated
from app.database.db_connect import get_db
from app.models.patient_model import Patient
from sqlalchemy.orm import Session
from datetime import date
from fastapi import APIRouter
from app.controllers.auth_controller import require_roles

router = APIRouter(prefix="/patients", tags=["Patients"])

class PatientInput(BaseModel):
    first_name: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]
    last_name: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]
    date_of_birth: date
    i_sex: int
    contact_number: Annotated[str, Field(max_length=15, strip_whitespace=True)]
    email_address: Annotated[EmailStr, Field(max_length=50)]
    address: Annotated[str, Field(strip_whitespace=True)]

def patient_exists(db: Session, email: str):
    return db.query(Patient).filter(Patient.email_address == email).first()

@router.get("/get_patient")
async def get_patient(
    i_patient: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    patient = db.query(Patient).filter(Patient.i_patient == i_patient).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient

@router.get("/list_patients")
async def list_patients(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    return db.query(Patient).all()

@router.post("/add_patient")
async def add_patient(
    patient: PatientInput,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    if patient_exists(db, patient.email_address):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient with that email already exists")
    new_patient = Patient(**patient.model_dump())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return {"i_patient": new_patient.i_patient}

@router.put("/update_patient")
async def update_patient(
    i_patient: int,
    patient: PatientInput,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    db_patient = db.query(Patient).filter(Patient.i_patient == i_patient).first()
    if not db_patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    existing_patient = patient_exists(db, patient.email_address)
    if existing_patient and existing_patient.i_patient != i_patient:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email address already in use")

    for key, value in patient.model_dump().items():
        setattr(db_patient, key, value)

    db.commit()
    db.refresh(db_patient)
    return {"i_patient": db_patient.i_patient}

@router.delete("/delete_patient")
async def delete_patient(
    i_patient: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    patient = db.query(Patient).filter(Patient.i_patient == i_patient).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    db.delete(patient)
    db.commit()
    return {"i_patient": i_patient}
