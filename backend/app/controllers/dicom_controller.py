from fastapi import HTTPException, status, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from typing import Annotated
from app.database.db_connect import config, get_db
from app.models.dicom_model import DICOM
from sqlalchemy.orm import Session
from fastapi import APIRouter
from app.controllers.auth_controller import require_roles
import os

CURRENT_DIR = os.path.dirname(__file__)
APP_ROOT = os.path.dirname(CURRENT_DIR)
DICOM_STORAGE_DIR = os.path.join(APP_ROOT, config["DICOM_STORAGE_DIR"])
ALLOWED_EXTENSIONS = {".zip", ".rar", ".tar", ".dcm"}
os.makedirs(DICOM_STORAGE_DIR, exist_ok=True)

router = APIRouter(prefix="/dicoms", tags=["DICOM files"])

class DICOMInputForm(BaseModel):
    i_patient: int
    file_name: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]
    i_file_type: int

def dicom_exists_by_filename(db: Session, file_name: str):
    return db.query(DICOM).filter(DICOM.file_name == file_name).first()

def is_allowed_file(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

@router.get("/get_dicom")
async def get_dicom(i_dicom: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    dicom = db.query(DICOM).filter(DICOM.i_dicom == i_dicom).first()
    if not dicom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DICOM not found"
        )
    return {"i_dicom": dicom.i_dicom, "i_patient": dicom.i_patient, "file_name": dicom.file_name}

@router.post("/add_dicom")
async def add_dicom(
    i_patient: int = Form(...),
    file_name: str = Form(...),
    i_file_type: int = Form(...),
    dicom_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    if not is_allowed_file(file_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip, .tar, or .dcm files are allowed"
        )

    if dicom_exists_by_filename(db, file_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DICOM with that file name already exists"
        )

    file_path = os.path.join(APP_ROOT, DICOM_STORAGE_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(await dicom_file.read())

    new_dicom = DICOM(i_patient=i_patient, path_to_dicom=file_path, i_file_type=i_file_type, file_name=file_name)
    db.add(new_dicom)
    db.commit()
    db.refresh(new_dicom)
    return {"i_dicom": new_dicom.i_dicom}

@router.put("/update_dicom")
async def update_dicom(
    i_dicom: int,
    file_name: str = Form(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    if not is_allowed_file(file_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip, .tar, or .dcm files are allowed"
        )

    db_dicom = db.query(DICOM).filter(DICOM.i_dicom == i_dicom).first()
    if not db_dicom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DICOM not found"
        )

    existing_dicom = dicom_exists_by_filename(db, file_name)
    if existing_dicom and existing_dicom.i_dicom != i_dicom:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File name already in use"
        )

    old_file_path = db_dicom.path_to_dicom
    new_file_path = os.path.join(APP_ROOT, DICOM_STORAGE_DIR, file_name)
    if os.path.exists(old_file_path):
        os.rename(old_file_path, new_file_path)

    db_dicom.file_name = file_name
    db_dicom.path_to_dicom = new_file_path

    db.commit()
    db.refresh(db_dicom)
    return {"i_dicom": db_dicom.i_dicom}

@router.delete("/delete_dicom")
async def delete_dicom(i_dicom: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    dicom = db.query(DICOM).filter(DICOM.i_dicom == i_dicom).first()
    if not dicom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DICOM not found"
        )

    if os.path.exists(dicom.path_to_dicom):
        os.remove(dicom.path_to_dicom)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DICOM not found in storage"
        )
    db.delete(dicom)
    db.commit()
    return {"i_dicom": i_dicom}

@router.get("/download_dicom")
async def download_dicom(i_dicom: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    dicom = db.query(DICOM).filter(DICOM.i_dicom == i_dicom).first()
    if not dicom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DICOM not found"
        )
    if not os.path.exists(dicom.path_to_dicom):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DICOM file not found in storage"
        )

    return FileResponse(dicom.path_to_dicom, filename=dicom.file_name)
