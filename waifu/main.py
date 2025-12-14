import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

from .handlers import register_handlers

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

async def main():
    register_handlers(client)
    print("Userbot запущен")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
