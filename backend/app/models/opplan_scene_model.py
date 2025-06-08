from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.db_connect import Base

class OperationPlanScenes(Base):
    __tablename__ = "Operation_Plan_Scenes"

    i_operation_plan = Column(Integer, ForeignKey("Operation_Plans.i_operation_plan"), primary_key=True)

    # Prosthesis transform (nullable)
    prosthesis_translation_x = Column(Float, nullable=True)
    prosthesis_translation_y = Column(Float, nullable=True)
    prosthesis_translation_z = Column(Float, nullable=True)
    prosthesis_rotation_x = Column(Float, nullable=True)
    prosthesis_rotation_y = Column(Float, nullable=True)
    prosthesis_rotation_z = Column(Float, nullable=True)
    prosthesis_scale_x = Column(Float, nullable=True)
    prosthesis_scale_y = Column(Float, nullable=True)
    prosthesis_scale_z = Column(Float, nullable=True)

    # Bone transform (not nullable, as bone is always present)
    bone_translation_x = Column(Float, nullable=False, default=0.0)
    bone_translation_y = Column(Float, nullable=False, default=0.0)
    bone_translation_z = Column(Float, nullable=False, default=0.0)
    bone_rotation_x = Column(Float, nullable=False, default=0.0)
    bone_rotation_y = Column(Float, nullable=False, default=0.0)
    bone_rotation_z = Column(Float, nullable=False, default=0.0)
    bone_scale_x = Column(Float, nullable=False, default=1.0)
    bone_scale_y = Column(Float, nullable=False, default=1.0)
    bone_scale_z = Column(Float, nullable=False, default=1.0)

#def __repr__(self):
#        return f"<OperationPlanScene(i_operation_plan={self.i_operation_plan})>"