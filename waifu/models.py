from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
)

class Base(DeclarativeBase):
    pass

# --- Таблица связей (Многие-ко-Многим) ---
# Связывает пользователей и чаты
chat_users = Table(
    'chat_users',
    Base.metadata,
    Column('user_id', BigInteger, ForeignKey('users.id'), primary_key=True),
    Column('chat_id', BigInteger, ForeignKey('chats.id'), primary_key=True)
)

# --- Таблица картинок (Аватарки) ---
class UserPic(Base):
    __tablename__ = "userpics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, unique=True)  # Путь к файлу на диске
    
    # Можно добавить created_at, если нужно

# --- Таблица Юзеры ---
class User(Base):
    __tablename__ = "users"

    # Telegram ID как Primary Key (без autoincrement, т.к. ID дает Телеграм)
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_bot = Column(Boolean, default=False)
    
    # Ссылка на таблицу юзерпиков
    avatar_id = Column(Integer, ForeignKey('userpics.id'), nullable=True)
    
    # Связи
    avatar = relationship("UserPic")
    chats = relationship("Chat", secondary=chat_users, back_populates="users")
    messages = relationship("MessageLog", back_populates="user")

# --- Таблица Чаты ---
class Chat(Base):
    __tablename__ = "chats"

    # Telegram Chat ID как Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    username = Column(String, nullable=True)
    
    # Ссылка на таблицу юзерпиков
    avatar_id = Column(Integer, ForeignKey('userpics.id'), nullable=True)
    
    # Связи
    avatar = relationship("UserPic")
    users = relationship("User", secondary=chat_users, back_populates="chats")
    messages = relationship("MessageLog", back_populates="chat")

# --- Таблица Сообщений (Обновленная) ---
class MessageLog(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Убрали chat_title, username, display_name.
    # chat_id и user_id теперь Foreign Keys.
    
    chat_id = Column(BigInteger, ForeignKey('chats.id'), index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True) # User может быть Null (напр. анонимный админ)
    
    message_id = Column(Integer)
    date = Column(DateTime(timezone=True))
    reply_info = Column(String)
    content = Column(Text)

    # Связи для удобного доступа (message.chat.title)
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")