from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

POSTGRES_PASSWORD = None

with open(os.getenv("POSTGRES_PASSWORD_FILE"), "r") as f:
    POSTGRES_PASSWORD = f.read().strip("\n")

url = "postgresql://postgres:" + POSTGRES_PASSWORD + "@db:5432/"
engine = create_engine(url)
Session = sessionmaker(bind=engine)

Base = declarative_base()
