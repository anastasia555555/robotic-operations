from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.db_connect import get_db
from app.models.opplan_model import OperationType, OperationPlan, OperationPlanBone, OperationPlanProsthesis
from app.models.bone_model import BoneModel
from app.models.prosthesis_model import ProsthesisModel
from typing import Optional
from datetime import datetime
from app.controllers.auth_controller import require_roles

router = APIRouter(prefix="/operation_plans", tags=["Operation Plans"])

class OperationPlanInput(BaseModel):
    i_operation_type: int
    i_patient: int
    name: Optional[str] = None

@router.get("/list_operation_types")
async def list_operation_types(db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    return db.query(OperationType).all()

@router.post("/add_opplan")
async def add_opplan(op: OperationPlanInput, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    plan_name = op.name or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_plan = OperationPlan(
        i_operation_type=op.i_operation_type,
        i_patient=op.i_patient,
        name=plan_name
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"i_operation_plan": new_plan.i_operation_plan}

@router.get("/get_opplan")
async def get_opplan(i_operation_plan: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    op = db.query(OperationPlan).filter(OperationPlan.i_operation_plan == i_operation_plan).first()
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation Plan not found")
    return op

@router.get("/list_operation_plans")
async def list_operation_plans(db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    return db.query(OperationPlan).all()

@router.delete("/delete_opplan")
async def delete_opplan(i_operation_plan: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    op = db.query(OperationPlan).filter(OperationPlan.i_operation_plan == i_operation_plan).first()
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation Plan not found")
    db.delete(op)
    db.commit()
    return {"i_operation_plan": i_operation_plan}

@router.put("/update_opplan")
async def update_opplan(i_operation_plan: int, op: OperationPlanInput, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    db_op = db.query(OperationPlan).filter(OperationPlan.i_operation_plan == i_operation_plan).first()
    if not db_op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation Plan not found")

    if db_op.i_operation_type != op.i_operation_type:
        db.query(OperationPlanProsthesis).filter(OperationPlanProsthesis.i_operation_plan == i_operation_plan).delete()

    if db_op.i_patient != op.i_patient:
        db.query(OperationPlanBone).filter(OperationPlanBone.i_operation_plan == i_operation_plan).delete()

    db_op.i_operation_type = op.i_operation_type
    db_op.i_patient = op.i_patient
    db_op.name = op.name
    db.commit()
    db.refresh(db_op)
    return {"i_operation_plan": db_op.i_operation_plan}

@router.post("/assign_bone_model")
async def assign_bone_model(i_operation_plan: int, i_3d_bone_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    op = db.query(OperationPlan).filter(OperationPlan.i_operation_plan == i_operation_plan).first()
    model = db.query(BoneModel).filter(BoneModel.i_3d_bone_model == i_3d_bone_model).first()
    if not op or not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation Plan or Bone Model not found")
    if op.i_patient != model.i_patient:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bone model must belong to same patient")
    db.add(OperationPlanBone(i_operation_plan=i_operation_plan, i_3d_bone_model=i_3d_bone_model))
    db.commit()
    return {"i_operation_plan": i_operation_plan, "i_3d_bone_model": i_3d_bone_model}

@router.post("/assign_prosthetic_model")
async def assign_prosthetic_model(i_operation_plan: int, i_3d_prosthesis_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    op = db.query(OperationPlan).filter(OperationPlan.i_operation_plan == i_operation_plan).first()
    model = db.query(ProsthesisModel).filter(ProsthesisModel.i_3d_prosthesis_model == i_3d_prosthesis_model).first()
    if not op or not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation Plan or Prosthesis Model not found")
    if op.i_operation_type != model.i_operation_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prosthesis model must have same operation type")
    db.add(OperationPlanProsthesis(i_operation_plan=i_operation_plan, i_3d_prosthesis_model=i_3d_prosthesis_model))
    db.commit()
    return {"i_operation_plan": i_operation_plan, "i_3d_prosthesis_model": i_3d_prosthesis_model}

@router.post("/unassign_bone_model")
async def unassign_bone_model(i_operation_plan: int, i_3d_bone_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    op_bone = db.query(OperationPlanBone).filter_by(i_operation_plan=i_operation_plan, i_3d_bone_model=i_3d_bone_model).first()
    if not op_bone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bone model not assigned to this operation plan")
    db.delete(op_bone)
    db.commit()
    return {"i_operation_plan": i_operation_plan, "i_3d_bone_model": i_3d_bone_model}

@router.post("/unassign_prosthesis_model")
async def unassign_prosthesis_model(i_operation_plan: int, i_3d_prosthesis_model: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    op_prosthesis = db.query(OperationPlanProsthesis).filter_by(i_operation_plan=i_operation_plan, i_3d_prosthesis_model=i_3d_prosthesis_model).first()
    if not op_prosthesis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prosthesis model not assigned to this operation plan")
    db.delete(op_prosthesis)
    db.commit()
    return {"i_operation_plan": i_operation_plan, "i_3d_prosthesis_model": i_3d_prosthesis_model}

@router.get("/list_assigned_bone_models")
async def list_assigned_bone_models(i_operation_plan: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    assigned_bones = db.query(BoneModel).join(OperationPlanBone).filter(OperationPlanBone.i_operation_plan == i_operation_plan).all()
    return [{
        "i_3d_bone_model": bone.i_3d_bone_model,
        "i_patient": bone.i_patient,
        "i_dicom": bone.i_dicom,
        "i_file_type": bone.i_file_type,
        "path_to_model": bone.path_to_model,
        "file_name": bone.file_name
    } for bone in assigned_bones]

@router.get("/list_assigned_prosthesis_models")
async def list_assigned_prosthesis_models(i_operation_plan: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    assigned_prosthesis = db.query(ProsthesisModel).join(OperationPlanProsthesis).filter(OperationPlanProsthesis.i_operation_plan == i_operation_plan).all()
    return [{
        "i_3d_prosthesis_model": prosthesis.i_3d_prosthesis_model,
        "i_operation_type": prosthesis.i_operation_type,
        "i_file_type": prosthesis.i_file_type,
        "path_to_model": prosthesis.path_to_model,
        "file_name": prosthesis.file_name,
        "i_bone": prosthesis.i_bone,
        "size": prosthesis.size,
        "poly": prosthesis.poly,
        "manufacturer": prosthesis.manufacturer
    } for prosthesis in assigned_prosthesis]
