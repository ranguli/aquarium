from sqlalchemy import Column, String, Integer, PrimaryKeyConstraint
from base import Base


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, autoincrement=True, primary_key=True)
    sha256 = Column(String)
    url = Column(String)
    seen = Column(String)
    PrimaryKeyConstraint(id, name="malware_pk")

    def __init__(self, sha256, url, seen):
        self.sha256 = sha256
        self.url = url
        self.seen = seen
