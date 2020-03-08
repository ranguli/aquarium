# coding=utf-8

from sqlalchemy import Column, String, Integer, PrimaryKeyConstraint
from base import Base


class Sample(Base):
    __tablename__ = "sample"

    sha256 = Column(String, primary_key=True)
    md5 = Column(String)
    filename = Column(String)
    filetype = Column(String)
    PrimaryKeyConstraint(sha256, name="hash_pk")

    def __init__(self, sha256, md5, filename, filetype):
        self.sha256 = sha256
        self.md5 = md5
        self.filename = filename
        self.filetype = filetype
