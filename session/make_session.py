from telethon import TelegramClient
import os
from dotenv import load_dotenv


load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")


with TelegramClient(
    "user",
    API_ID,
    API_HASH,
    device_model="MyApp",
    system_version="Debian 12",
    app_version="MyUserbot 1.0",
    lang_code="ru"
) as client:
    print("Session created")
