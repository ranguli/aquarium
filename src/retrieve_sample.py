from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from base import Session, engine, Base
from sample import Sample
from source import Source


Base.metadata.create_all(engine)
session = Session()


with open(sample.filename, "wb") as f:
    f.write(sample.sample)
    
