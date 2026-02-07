from sqlalchemy import Column, Text, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    role = Column(Text)
    current_question = Column(Integer)
    status = Column(Text)
    created_at = Column(TIMESTAMP)
