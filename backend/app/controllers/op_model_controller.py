from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.database.db_connect import get_db
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database.db_connect import config
from app.services.op_model_service import create_model_handler, remove_model_handler, restore_positions, scene_handlers, decompose_matrix, compose_matrix
from app.models.opplan_scene_model import OperationPlanScenes
from app.models.prosthesis_model import ProsthesisModel
from app.controllers.auth_controller import require_roles

CURRENT_DIR = os.path.dirname(__file__)
APP_ROOT = os.path.dirname(CURRENT_DIR)
VIEW_SNAPSHOTS_STORAGE_DIR = os.path.join(APP_ROOT, config["VIEW_SNAPSHOTS_STORAGE_DIR"])

router = APIRouter(prefix="/operation_plan_models", tags=["Operation Plan Models"])

class SlideRequest(BaseModel):
    i_operation_plan: int
    direction: str
    value: float

class ProsthesisAssignmentRequest(BaseModel):
    i_operation_plan: int
    i_3d_prosthesis_model: int

class ScaleRequest(BaseModel):
    i_operation_plan: int
    scale_x: float
    scale_y: float
    scale_z: float

class RotateRequest(BaseModel):
    i_operation_plan: int
    axis: str
    angle: float

@router.post("/create_handler")
def create_handler(i_operation_plan: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    try:
        create_model_handler(i_operation_plan, db)
        return {"status": "handler created", "message": "Bone model loaded. Checking for assigned prosthesis."}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/remove_handler")
def remove_handler(i_operation_plan: int, _: dict = Depends(require_roles(1, 2))):
    remove_model_handler(i_operation_plan)
    return {"status": "handler removed"}

@router.post("/assign_prosthesis")
def assign_prosthesis(request: ProsthesisAssignmentRequest, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    if request.i_operation_plan not in scene_handlers:
        create_model_handler(request.i_operation_plan, db)

    handler = scene_handlers[request.i_operation_plan]

    prosthesis_model_db = db.query(ProsthesisModel).filter_by(i_3d_prosthesis_model=request.i_3d_prosthesis_model).first()
    if not prosthesis_model_db:
        raise HTTPException(status_code=404, detail="Prosthesis model not found.")

    try:
        handler.add_prosthesis_to_scene(prosthesis_model_db.path_to_model)
        return {"status": "success", "message": "Prosthesis added/changed in scene."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add prosthesis to scene: {str(e)}")

@router.post("/remove_prosthesis")
def remove_prosthesis(i_operation_plan: int, _: dict = Depends(require_roles(1, 2))):
    if i_operation_plan not in scene_handlers:
        raise HTTPException(status_code=404, detail="Model handler not found for this operation plan.")

    handler = scene_handlers[i_operation_plan]
    try:
        handler.remove_prosthesis_from_scene()
        return {"status": "success", "message": "Prosthesis removed from scene."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove prosthesis from scene: {str(e)}")

@router.post("/slide")
def slide(data: SlideRequest, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    if data.i_operation_plan not in scene_handlers:
        create_model_handler(data.i_operation_plan, db)

    handler = scene_handlers[data.i_operation_plan]

    if not handler.prosthesis_actor:
        raise HTTPException(status_code=400, detail="No prosthesis model is currently loaded in the scene to slide.")

    directions = {
        "up": handler.slide_prosthesis_up,
        "down": handler.slide_prosthesis_down,
        "left": handler.slide_prosthesis_left,
        "right": handler.slide_prosthesis_right,
        "forward": handler.slide_prosthesis_forward,
        "backward": handler.slide_prosthesis_backward,
    }
    if data.direction not in directions:
        raise HTTPException(status_code=400, detail="Invalid direction")

    directions[data.direction](data.value)
    return {"status": "moved"}

@router.post("/scale")
def scale_prosthesis(data: ScaleRequest, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    if data.i_operation_plan not in scene_handlers:
        try:
            create_model_handler(data.i_operation_plan, db)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Model handler not found and could not be created: {str(e)}")

    handler = scene_handlers[data.i_operation_plan]

    if not handler.prosthesis_actor:
        raise HTTPException(status_code=400, detail="No prosthesis model is currently loaded in the scene to scale.")

    try:
        handler.scale_prosthesis(data.scale_x, data.scale_y, data.scale_z)
        return {"status": "scaled", "message": f"Prosthesis scaled to ({data.scale_x}, {data.scale_y}, {data.scale_z})."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scale prosthesis: {str(e)}")

@router.post("/rotate")
def rotate_prosthesis(data: RotateRequest, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    if data.i_operation_plan not in scene_handlers:
        create_model_handler(data.i_operation_plan, db)

    handler = scene_handlers[data.i_operation_plan]

    if not handler.prosthesis_actor:
        raise HTTPException(status_code=400, detail="No prosthesis model is currently loaded in the scene to rotate.")

    try:
        handler.rotate_prosthesis(data.axis.lower(), data.angle)
        return {"status": "rotated", "message": f"Prosthesis rotated {data.angle}° around {data.axis}-axis."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get_view")
def get_view(i_operation_plan: int, view_name: str, db: Session = Depends(get_db), width: int = 1200, height: int = 800, _: dict = Depends(require_roles(1, 2))):
    if i_operation_plan not in scene_handlers:
        create_model_handler(i_operation_plan, db)

    handler = scene_handlers[i_operation_plan]
    handler.set_camera(view_name)
    handler.render_window.SetSize(width, height)
    filepath = os.path.join(APP_ROOT, VIEW_SNAPSHOTS_STORAGE_DIR, f"scene_{i_operation_plan}_{view_name}.png")
    handler.render_to_image(filepath)

    return FileResponse(filepath, media_type="image/png")

@router.post("/save_positions")
def save_positions(i_operation_plan: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    if i_operation_plan not in scene_handlers:
        raise HTTPException(status_code=404, detail="Handler not loaded")

    handler = scene_handlers[i_operation_plan]

    prosthesis_matrix = handler.get_prosthesis_matrix()
    bone_matrix = handler.get_bone_matrix()

    scene = db.query(OperationPlanScenes).filter_by(i_operation_plan=i_operation_plan).first()
    if not scene:
        scene = OperationPlanScenes(i_operation_plan=i_operation_plan)
        db.add(scene)

    if prosthesis_matrix:
        pt, pr, ps = decompose_matrix(prosthesis_matrix)
        scene.prosthesis_translation_x, scene.prosthesis_translation_y, scene.prosthesis_translation_z = map(float, pt)
        scene.prosthesis_rotation_x, scene.prosthesis_rotation_y, scene.prosthesis_rotation_z = map(float, pr)
        scene.prosthesis_scale_x, scene.prosthesis_scale_y, scene.prosthesis_scale_z = map(float, ps)
    else:
        scene.prosthesis_translation_x = scene.prosthesis_translation_y = scene.prosthesis_translation_z = None
        scene.prosthesis_rotation_x = scene.prosthesis_rotation_y = scene.prosthesis_rotation_z = None
        scene.prosthesis_scale_x = scene.prosthesis_scale_y = scene.prosthesis_scale_z = None

    bt, br, bs = decompose_matrix(bone_matrix)
    scene.bone_translation_x, scene.bone_translation_y, scene.bone_translation_z = map(float, bt)
    scene.bone_rotation_x, scene.bone_rotation_y, scene.bone_rotation_z = map(float, br)
    scene.bone_scale_x, scene.bone_scale_y, scene.bone_scale_z = map(float, bs)

    db.commit()
    return {"status": "saved"}

@router.post("/restore_positions")
def restore_positions_api(i_operation_plan: int, db: Session = Depends(get_db), _: dict = Depends(require_roles(1, 2))):
    try:
        restore_positions(i_operation_plan, db)
        return {"status": "success", "message": f"Positions restored for operation plan {i_operation_plan}"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore positions: {str(e)}")
