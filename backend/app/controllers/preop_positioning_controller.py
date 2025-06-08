from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.controllers.auth_controller import require_roles
from app.models.regpoint_model import RegistrationPoint
import numpy as np
from app.services.preop_positioning_service import positioning_handlers, PositioningHandler
from app.database.db_connect import get_db
from app.models.opplan_model import OperationPlanBone
from app.models.bone_model import BoneModel

router = APIRouter(
    prefix="/preop_bone_positioning",
    tags=["PreOp Bone Positioning"]
)

class Point3D(BaseModel):
    x: float
    y: float
    z: float

class RegisterPointRequest(BaseModel):
    i_operation_plan: int
    index: int
    world_coords: Point3D

class PredictionErrorRequest(BaseModel):
    i_operation_plan: int
    actual_coords: list[Point3D]

surface_sorting = {
    "top": ("z", True),
    "bottom": ("z", False),
    "front": ("y", True),
    "back": ("y", False),
    "other side": ("x", True),
    "side": ("x", False)
}

@router.post("/create_handler")
def create_handler(
    i_operation_plan: int,
    view_name: str = Query("top"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    if i_operation_plan in positioning_handlers:
        return {"status": "already initialized"}

    if view_name not in surface_sorting:
        raise HTTPException(status_code=400, detail=f"Invalid view_name: {view_name}")

    axis, descending = surface_sorting[view_name]
    op_bone = db.query(OperationPlanBone).filter_by(i_operation_plan=i_operation_plan).first()
    if not op_bone:
        raise HTTPException(status_code=404, detail="No OperationPlanBone found")
    bone_model = db.query(BoneModel).filter_by(
        i_3d_bone_model=op_bone.i_3d_bone_model
    ).first()
    if not bone_model:
        raise HTTPException(status_code=404, detail="Bone model not found")

    try:
        handler = PositioningHandler(
            nrrd_path=bone_model.path_to_model,
            axis=axis,
            descending=descending
        )
        positioning_handlers[i_operation_plan] = handler
        return {
            "status": "handler created",
            "message": f"Bone model loaded and 10 surface points sampled for view '{view_name}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/remove_handler")
def remove_handler(
    i_operation_plan: int,
    _: dict = Depends(require_roles(1, 2))
):
    from app.services.preop_positioning_service import remove_positioning_handler
    if remove_positioning_handler(i_operation_plan):
        return {"status": "handler removed"}
    raise HTTPException(status_code=404, detail="Handler not found")


@router.post("/register_point")
def register_point(
    data: RegisterPointRequest,
    _: dict = Depends(require_roles(1, 2))
):
    handler = positioning_handlers.get(data.i_operation_plan)
    if not handler:
        raise HTTPException(status_code=404, detail="Handler not initialized")

    try:
        handler.register_point(
            data.index,
            [data.world_coords.x, data.world_coords.y, data.world_coords.z]
        )
        response = {
            "status": "registered",
            "total_registered": len(handler.registered_points)
        }
        if handler.prediction_points and len(handler.registered_points) == 10:
            response["prediction_indices"] = handler.prediction_points
        if hasattr(handler, 'prediction_errors') and handler.prediction_errors is not None:
            response["prediction_errors"] = handler.prediction_errors
            response["mean_error"] = float(np.mean(handler.prediction_errors))
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evaluate_predictions")
def evaluate_predictions(
    data: PredictionErrorRequest,
    _: dict = Depends(require_roles(1, 2))
):
    handler = positioning_handlers.get(data.i_operation_plan)
    if not handler:
        raise HTTPException(status_code=404, detail="Handler not initialized")

    if not handler.predicted_world_coords:
        raise HTTPException(status_code=400, detail="Need 10 points first to generate predictions")

    actual_coords = [[pt.x, pt.y, pt.z] for pt in data.actual_coords]
    errors = handler.get_prediction_error(actual_coords)
    return {"errors": errors, "mean_error": float(np.mean(errors))}


@router.get("/get_view")
def get_view(
    i_operation_plan: int,
    view_name: str = Query("front"),
    width: int = Query(1200),
    height: int = Query(800),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    handler = positioning_handlers.get(i_operation_plan)
    if not handler:
        if view_name not in surface_sorting:
            raise HTTPException(status_code=400, detail=f"Invalid view_name: {view_name}")
        axis, descending = surface_sorting[view_name]
        op_bone = db.query(OperationPlanBone).filter_by(i_operation_plan=i_operation_plan).first()
        if not op_bone:
            raise HTTPException(status_code=404, detail="No OperationPlanBone found")
        bone_model = db.query(BoneModel).filter_by(
            i_3d_bone_model=op_bone.i_3d_bone_model
        ).first()
        if not bone_model:
            raise HTTPException(status_code=404, detail="Bone model not found")
        try:
            handler = PositioningHandler(
                nrrd_path=bone_model.path_to_model,
                axis=axis,
                descending=descending
            )
            positioning_handlers[i_operation_plan] = handler
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Handler creation failed: {str(e)}")

    handler.set_camera(view_name)
    handler.render_window.SetSize(width, height)
    image_bytes = handler.render_png_bytes()
    return Response(content=image_bytes, media_type="image/png")


@router.get("/get_points_status")
def get_points_status(i_operation_plan: int, _: dict = Depends(require_roles(1, 2))):
    handler = positioning_handlers.get(i_operation_plan)
    if not handler:
        raise HTTPException(status_code=404, detail="Handler not initialized")

    try:
        return handler.get_all_points_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save_registered_points")
def store_registered_points(
    i_operation_plan: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    handler = positioning_handlers.get(i_operation_plan)
    if not handler:
        raise HTTPException(status_code=404, detail="Handler not initialized")

    if len(handler.registered_points) < 10:
        raise HTTPException(status_code=400, detail="All 10 points must be registered first.")

    existing = db.query(RegistrationPoint).filter_by(i_operation_plan=i_operation_plan).all()
    if existing:
        raise HTTPException(status_code=400, detail="Points already stored for this operation plan.")

    try:
        for idx, model_pt, world_pt in handler.get_registered_main_points():
            db.add(RegistrationPoint(
                i_operation_plan=i_operation_plan,
                point_index=int(idx),
                model_x=float(model_pt[0]),
                model_y=float(model_pt[1]),
                model_z=float(model_pt[2]),
                world_x=float(world_pt[0]),
                world_y=float(world_pt[1]),
                world_z=float(world_pt[2]),
            ))
        db.commit()
        return {"status": "points stored"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove_registered_points")
def remove_registered_points(
    i_operation_plan: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(1, 2))
):
    deleted = db.query(RegistrationPoint).filter_by(i_operation_plan=i_operation_plan).delete()
    db.commit()
    
    return {
        "status": "deleted",
        "deleted_count": deleted
    }
