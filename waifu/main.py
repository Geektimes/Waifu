import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

from .handlers import register_handlers
from .db import engine
from .models import Base

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "session/user"

# Создаем папку для аватарок, если её нет
os.makedirs("session/avatars", exist_ok=True)

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
    device_model="MyApp",
    system_version="Debian 12",
    app_version="MyUserbot 1.0",
    lang_code="ru"
)

async def init_db():
    """Создает таблицы в БД"""
    async with engine.begin() as conn:
        # ВНИМАНИЕ: Если меняется структура таблиц, старые таблицы нужно удалить.
        # Для продакшена используйте Alembic. Для теста можно раскомментировать:
        # await conn.run_sync(Base.metadata.drop_all) 
        
        await conn.run_sync(Base.metadata.create_all)

async def main():
    await init_db()
    print("База данных инициализирована.")
    
    register_handlers(client)
    print("Userbot запущен")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())