from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import os


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    with open(os.path.abspath(config_path), "r") as file:        
            return json.load(file)

config = load_config()

DATABASE_URL = config["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()