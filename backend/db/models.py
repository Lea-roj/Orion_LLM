from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content = Column(Text)
    graph_json = Column(Text)
    status = Column(String, default="TRANSLATING")
    translated_pdf = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
