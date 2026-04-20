from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float

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
    processed_chunks = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
