from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP
from datetime import datetime
from app.database.db_connect import Base


class Sex(Base):
    __tablename__ = "Sexes"
    i_sex = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, unique=True)


class Patient(Base):
    __tablename__ = "Patients"
    i_patient = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date)
    i_sex = Column(Integer, default=3)
    contact_number = Column(String(15))
    email_address = Column(String(50), unique=True)
    address = Column(Text)
    date_created = Column(TIMESTAMP, default=datetime.now)
