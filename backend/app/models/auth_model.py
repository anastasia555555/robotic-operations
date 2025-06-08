from sqlalchemy import ForeignKey, Column, Integer, String
from app.database.db_connect import Base


class User_Roles(Base):
    __tablename__ = "User_Roles"
    i_user_role = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True) 

class User(Base):
    __tablename__ = "Users"
    i_user = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email_address = Column(String(100))
    password_hash = Column(String(255))
    i_user_role = Column(Integer, ForeignKey("User_Roles.i_user_role"))