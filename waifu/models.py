from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime

class Base(DeclarativeBase):
    pass

class MessageLog(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    chat_id = Column(BigInteger, index=True)
    chat_title = Column(String)
    message_id = Column(Integer)
    
    # ВАЖНО: Добавляем timezone=True
    date = Column(DateTime(timezone=True))
    
    user_id = Column(BigInteger)
    username = Column(String)
    display_name = Column(String)
    reply_info = Column(String)
    content = Column(Text)