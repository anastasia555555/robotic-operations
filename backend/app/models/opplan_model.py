from sqlalchemy import Column, Integer, String, Text, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.database.db_connect import Base


class OperationType(Base):
    __tablename__ = "Operation_Types"
    i_operation_type = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)


class OperationPlan(Base):
    __tablename__ = "Operation_Plans"
    i_operation_plan = Column(Integer, primary_key=True)
    i_operation_type = Column(Integer, ForeignKey("Operation_Types.i_operation_type"), nullable=False)
    name = Column(String(100), nullable=False)
    i_patient = Column(Integer, ForeignKey("Patients.i_patient"))

#def __repr__(self):
#    return f"<OperationPlan(i_operation_plan={self.i_operation_plan}, name='{self.name}')>"



class OperationPlanBone(Base):
    __tablename__ = "Operation_Plan_Bone"
    i_operation_plan = Column(Integer, ForeignKey("Operation_Plans.i_operation_plan", ondelete="CASCADE"), nullable=False)
    i_3d_bone_model = Column(Integer, ForeignKey("3D_Bone_Models.i_3d_bone_model", ondelete="CASCADE"), nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint("i_operation_plan", "i_3d_bone_model", name="Operation_Plan_Bone_pkey"),)

class OperationPlanProsthesis(Base):
    __tablename__ = "Operation_Plan_Prosthesis"
    i_operation_plan = Column(Integer, ForeignKey("Operation_Plans.i_operation_plan", ondelete="CASCADE"), nullable=False)
    i_3d_prosthesis_model = Column(Integer, ForeignKey("3D_Prosthesis_Models.i_3d_prosthesis_model", ondelete="CASCADE"), nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint("i_operation_plan", "i_3d_prosthesis_model", name="Operation_Plan_Prosthesis_pkey"),)