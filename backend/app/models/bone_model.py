from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database.db_connect import Base


class FileType(Base):
    __tablename__ = "File_Types"
    i_file_type = Column(Integer, primary_key=True)
    file_extension = Column(String(10), nullable=False, unique=True)
    name = Column(String(50), nullable=False, default='Unknown')


class BoneModel(Base):
    __tablename__ = "3D_Bone_Models"
    i_3d_bone_model = Column(Integer, primary_key=True)
    i_patient = Column(Integer, ForeignKey("Patients.i_patient"))
    i_dicom = Column(Integer, ForeignKey("DICOMs.i_dicom"))
    i_file_type = Column(Integer, ForeignKey("File_Types.i_file_type"))
    path_to_model = Column(Text, nullable=False)
    file_name = Column(String(50), nullable=False, unique=True)
