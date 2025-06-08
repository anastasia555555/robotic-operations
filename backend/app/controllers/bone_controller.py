from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated
from app.database.db_connect import get_db, config
from app.models.bone_model import BoneModel
from app.controllers.auth_controller import require_roles
import os


CURRENT_DIR = os.path.dirname(__file__)
APP_ROOT = os.path.dirname(CURRENT_DIR)
BONE_STORAGE_DIR = os.path.join(APP_ROOT, config["BONE_STORAGE_DIR"])
ALLOWED_EXTENSIONS = {".nrrd"}
os.makedirs(BONE_STORAGE_DIR, exist_ok=True)

router = APIRouter(prefix="/3d_bone_models", tags=["3D Bone models"])

class BoneModelInputForm(BaseModel):
    i_patient: int
    i_dicom: int
    i_file_type: int
    file_name: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]


def bone_model_exists_by_filename(db: Session, file_name: str):
    return db.query(BoneModel).filter(BoneModel.file_name == file_name).first()

def is_allowed_file(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

@router.get("/get_model")
async def get_bone_model(i_3d_bone_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    model = db.query(BoneModel).filter(BoneModel.i_3d_bone_model == i_3d_bone_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Bone Model not found")
    return {
        "i_3d_bone_model": model.i_3d_bone_model,
        "i_patient": model.i_patient,
        "file_name": model.file_name,
    }

@router.get("/list_by_patient")
async def list_bone_models_by_patient(i_patient: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    models = db.query(BoneModel).filter(BoneModel.i_patient == i_patient).all()
    return models

@router.post("/add_model")
async def add_bone_model(
    i_patient: int = Form(...),
    i_dicom: int = Form(...),
    i_file_type: int = Form(...),
    file_name: str = Form(...),
    model_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    if not is_allowed_file(file_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .nrrd files are allowed")

    if bone_model_exists_by_filename(db, file_name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bone model with that file name already exists")

    file_path = os.path.join(BONE_STORAGE_DIR, file_name)

    with open(file_path, "wb") as f:
        while content := await model_file.read(1024 * 1024):
            f.write(content)

    new_model = BoneModel(
        i_patient=i_patient,
        i_dicom=i_dicom,
        i_file_type=i_file_type,
        file_name=file_name,
        path_to_model=file_path
    )
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return {"i_3d_bone_model": new_model.i_3d_bone_model}

@router.put("/update_model")
async def update_bone_model(i_3d_bone_model: int, file_name: str = Form(...), db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    if not is_allowed_file(file_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .nrrd files are allowed")

    model = db.query(BoneModel).filter(BoneModel.i_3d_bone_model == i_3d_bone_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Bone Model not found")

    existing = bone_model_exists_by_filename(db, file_name)
    if existing and existing.i_3d_bone_model != i_3d_bone_model:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File name already in use")

    old_file_path = model.path_to_model
    new_file_path = os.path.join(BONE_STORAGE_DIR, file_name)
    if os.path.exists(old_file_path):
        os.rename(old_file_path, new_file_path)

    model.file_name = file_name
    model.path_to_model = new_file_path
    db.commit()
    db.refresh(model)
    return {"i_3d_bone_model": model.i_3d_bone_model}

@router.delete("/delete_model")
async def delete_bone_model(i_3d_bone_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    model = db.query(BoneModel).filter(BoneModel.i_3d_bone_model == i_3d_bone_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Bone Model not found")

    if os.path.exists(model.path_to_model):
        os.remove(model.path_to_model)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model file not found in storage")

    db.delete(model)
    db.commit()
    return {"i_3d_bone_model": i_3d_bone_model}

@router.get("/download_model")
async def download_bone_model(i_3d_bone_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    model = db.query(BoneModel).filter(BoneModel.i_3d_bone_model == i_3d_bone_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Bone Model not found")

    if not os.path.exists(model.path_to_model):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model file not found in storage")

    return FileResponse(model.path_to_model, filename=model.file_name)
