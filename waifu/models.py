from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String

class Base(DeclarativeBase):
    pass


class MessageLog(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    chat = Column(String)
    text = Column(String)
