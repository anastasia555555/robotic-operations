from fastapi import FastAPI
from app.database.db_connect import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.controllers.patient_controller import router as patients_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.dicom_controller import router as dicom_router
from app.controllers.bone_controller import router as bone_model_router
from app.controllers.prosthesis_controller import router as prosthesis_model_router
from app.controllers.opplan_controller import router as operation_plan_router
from app.controllers.op_model_controller import router as op_model_router
from app.controllers.preop_positioning_controller import router as preop_positioning_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="RobOp API",
    description="API for managing patients, operations, DICOMs, and 3D models",
    version="1.0.0"
)

app.include_router(patients_router)
app.include_router(auth_router)
app.include_router(dicom_router)
app.include_router(bone_model_router)
app.include_router(prosthesis_model_router)
app.include_router(operation_plan_router)
app.include_router(op_model_router)
app.include_router(preop_positioning_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
