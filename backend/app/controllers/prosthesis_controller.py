from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated
from app.database.db_connect import get_db, config
from app.models.prosthesis_model import ProsthesisModel, Bone
from app.controllers.auth_controller import require_roles
import os

CURRENT_DIR = os.path.dirname(__file__)
APP_ROOT = os.path.dirname(CURRENT_DIR)
PROSTHESIS_STORAGE_DIR = os.path.join(APP_ROOT, config["PROSTHESIS_STORAGE_DIR"])
ALLOWED_EXTENSIONS = {".obj"}
os.makedirs(PROSTHESIS_STORAGE_DIR, exist_ok=True)

router = APIRouter(prefix="/3d_prosthesis_models", tags=["3D Prosthesis models"])

class ProsthesisModelInputForm(BaseModel):
    i_operation_type: int
    i_file_type: int
    i_bone: int
    file_name: Annotated[str, Field(min_length=1, max_length=50, strip_whitespace=True)]
    size: int
    poly: Annotated[str, Field(min_length=1, max_length=10, strip_whitespace=True)]
    manufacturer: Annotated[str, Field(min_length=1, max_length=100, strip_whitespace=True)]

def prosthesis_model_exists_by_filename(db: Session, file_name: str):
    return db.query(ProsthesisModel).filter(ProsthesisModel.file_name == file_name).first()

def is_allowed_file(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

@router.get("/get_model")
async def get_prosthesis_model(i_3d_prosthesis_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    model = db.query(ProsthesisModel).filter(ProsthesisModel.i_3d_prosthesis_model == i_3d_prosthesis_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Prosthesis Model not found")
    return {
        "i_3d_prosthesis_model": model.i_3d_prosthesis_model,
        "i_operation_type": model.i_operation_type,
        "file_name": model.file_name,
        "i_bone": model.i_bone,
        "size": model.size,
        "poly": model.poly,
        "manufacturer": model.manufacturer
    }

@router.post("/add_model")
async def add_prosthesis_model(
    i_operation_type: int = Form(...),
    i_file_type: int = Form(...),
    i_bone: int = Form(...),
    file_name: str = Form(...),
    size: int = Form(...),
    poly: str = Form(...),
    manufacturer: str = Form(...),
    model_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    if not is_allowed_file(file_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .obj files are allowed")

    if prosthesis_model_exists_by_filename(db, file_name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prosthesis model with that file name already exists")

    bone = db.query(Bone).filter(Bone.i_bone == i_bone).first()
    if not bone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bone not found")

    file_path = os.path.join(PROSTHESIS_STORAGE_DIR, file_name)
    with open(file_path, "wb") as f:
        while content := await model_file.read(1024 * 1024):
            f.write(content)

    new_model = ProsthesisModel(
        i_operation_type=i_operation_type,
        i_file_type=i_file_type,
        i_bone=i_bone,
        file_name=file_name,
        size=size,
        poly=poly,
        manufacturer=manufacturer,
        path_to_model=file_path
    )
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return {"i_3d_prosthesis_model": new_model.i_3d_prosthesis_model}

@router.put("/update_model")
async def update_prosthesis_model(
    i_3d_prosthesis_model: int,
    file_name: str = Form(...),
    i_bone: int = Form(...),
    size: int = Form(...),
    poly: str = Form(...),
    manufacturer: str = Form(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    if not is_allowed_file(file_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .obj files are allowed")

    model = db.query(ProsthesisModel).filter(ProsthesisModel.i_3d_prosthesis_model == i_3d_prosthesis_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Prosthesis Model not found")

    bone = db.query(Bone).filter(Bone.i_bone == i_bone).first()
    if not bone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bone not found")

    existing = prosthesis_model_exists_by_filename(db, file_name)
    if existing and existing.i_3d_prosthesis_model != i_3d_prosthesis_model:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File name already in use")

    old_file_path = model.path_to_model
    new_file_path = os.path.join(PROSTHESIS_STORAGE_DIR, file_name)
    if os.path.exists(old_file_path):
        os.rename(old_file_path, new_file_path)

    model.file_name = file_name
    model.i_bone = i_bone
    model.size = size
    model.poly = poly
    model.manufacturer = manufacturer
    model.path_to_model = new_file_path
    db.commit()
    db.refresh(model)
    return {"i_3d_prosthesis_model": model.i_3d_prosthesis_model}

@router.delete("/delete_model")
async def delete_prosthesis_model(i_3d_prosthesis_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    model = db.query(ProsthesisModel).filter(ProsthesisModel.i_3d_prosthesis_model == i_3d_prosthesis_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Prosthesis Model not found")

    if os.path.exists(model.path_to_model):
        os.remove(model.path_to_model)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model file not found in storage")

    db.delete(model)
    db.commit()
    return {"i_3d_prosthesis_model": i_3d_prosthesis_model}

@router.get("/download_model")
async def download_prosthesis_model(i_3d_prosthesis_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    model = db.query(ProsthesisModel).filter(ProsthesisModel.i_3d_prosthesis_model == i_3d_prosthesis_model).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="3D Prosthesis Model not found")

    if not os.path.exists(model.path_to_model):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model file not found in storage")

    return FileResponse(model.path_to_model, filename=model.file_name)

@router.get("/list_by_operation_type")
async def list_by_operation_type(i_operation_type: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    models = db.query(ProsthesisModel).filter(ProsthesisModel.i_operation_type == i_operation_type).all()

    if not models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No 3D Prosthesis Models found for the given operation type")

    return [
        {
            "i_3d_prosthesis_model": model.i_3d_prosthesis_model,
            "i_operation_type": model.i_operation_type,
            "file_name": model.file_name,
            "i_bone": model.i_bone,
            "size": model.size,
            "poly": model.poly,
            "manufacturer": model.manufacturer
        }
        for model in models
    ]

@router.get("/get_model_filtered")
async def get_model_filtered(
    manufacturer: str = None,
    size: int = None,
    poly: str = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    query = db.query(ProsthesisModel)

    if manufacturer:
        query = query.filter(ProsthesisModel.manufacturer == manufacturer)
    if size:
        query = query.filter(ProsthesisModel.size == size)
    if poly:
        query = query.filter(ProsthesisModel.poly == poly)

    models = query.all()

    if not models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No 3D Prosthesis Models found with the given details")

    return [
        {
            "i_3d_prosthesis_model": model.i_3d_prosthesis_model,
            "i_operation_type": model.i_operation_type,
            "file_name": model.file_name,
            "i_bone": model.i_bone,
            "size": model.size,
            "poly": model.poly,
            "manufacturer": model.manufacturer
        }
        for model in models
    ]
