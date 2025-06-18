from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from app.database.db_connect import Base

class RegistrationPoint(Base):
    __tablename__ = "Registration_Points"

    i_registration_point = Column(Integer, primary_key=True, index=True)
    i_operation_plan = Column(Integer, ForeignKey("Operation_Plans.i_operation_plan", ondelete="CASCADE"), nullable=False)
    point_index = Column(Integer, nullable=False)
    
    model_x = Column(Float, nullable=False)
    model_y = Column(Float, nullable=False)
    model_z = Column(Float, nullable=False)
    
    world_x = Column(Float, nullable=False)
    world_y = Column(Float, nullable=False)
    world_z = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("i_operation_plan", "point_index", name="uq_registration_point"),
    )

