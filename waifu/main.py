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
    """Создает таблицы в БД, если их нет"""
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Раскомментировать, если надо очистить БД
        await conn.run_sync(Base.metadata.create_all)

async def main():
    # Сначала инициализируем БД
    await init_db()
    print("База данных инициализирована.")
    
    register_handlers(client)
    print("Userbot запущен")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())