from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database.db_connect import Base


class ProsthesisModel(Base):
    __tablename__ = "3D_Prosthesis_Models"
    i_3d_prosthesis_model = Column(Integer, primary_key=True)
    i_operation_type = Column(Integer, ForeignKey("Operation_Types.i_operation_type"))
    i_file_type = Column(Integer, ForeignKey("File_Types.i_file_type"))
    path_to_model = Column(Text, nullable=False)
    file_name = Column(String(50), nullable=False, unique=True)
    i_bone = Column(Integer, ForeignKey("Bones.i_bone"))
    size = Column(Integer, nullable=False)
    poly = Column(String(10), nullable=False)
    manufacturer = Column(String(100), nullable=False, default='Unknown')

class Bone(Base):
    __tablename__ = "Bones"
    i_bone = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
