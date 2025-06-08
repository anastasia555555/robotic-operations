from sqlalchemy import Column, Integer, Text, ForeignKey, String
from app.database.db_connect import Base


class DICOM(Base):
    __tablename__ = "DICOMs"
    i_dicom = Column(Integer, primary_key=True, index=True)
    i_patient = Column(Integer, ForeignKey("Patients.i_patient"), nullable=False)
    path_to_dicom = Column(Text, nullable=False)
    file_name = Column(String(50), nullable=False, unique=True)
    i_file_type = Column(Integer, ForeignKey("File_Types.i_file_type"), nullable=False)