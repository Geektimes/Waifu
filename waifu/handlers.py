import logging
import asyncio
from telethon import events
from telethon.errors import FloodWaitError
from sqlalchemy.future import select

# Импортируем нашу сессию и модель
from .db import SessionLocal
from .models import MessageLog

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def register_handlers(client):

    @client.on(events.NewMessage(pattern="/ping"))
    async def ping(event):
        await event.reply("pong")

    @client.on(events.ChatAction)
    async def on_added_to_chat(event):
        if not (event.user_added or event.user_joined or event.created):
            return

        try:
            me = await client.get_me()
            if me.id not in event.user_ids:
                return
        except Exception:
            return

        logger.info("Бот вступил в чат. Ожидание 5 сек...")
        await asyncio.sleep(5)

        try:
            chat = await client.get_entity(event.chat_id)
        except Exception as e:
            logger.error(f"Ошибка получения чата: {e}")
            return

        chat_title = getattr(chat, 'title', f'Chat_{chat.id}')
        chat_username = getattr(chat, 'username', None)
        
        logger.info(f"Начинаю скачивание в БД: {chat_title}")

        # Открываем сессию БД
        async with SessionLocal() as db_session:
            try:
                batch = []
                total_count = 0

                async for message in client.iter_messages(chat, reverse=True):
                    
                    # --- ПОДГОТОВКА ДАННЫХ ---
                    
                    # User Info
                    sender = await message.get_sender()
                    user_id = 0
                    username = None
                    display_name = "Unknown"

                    if sender:
                        user_id = sender.id
                        username = getattr(sender, 'username', None)
                        
                        first = getattr(sender, 'first_name', '') or getattr(sender, 'title', '')
                        last = getattr(sender, 'last_name', '') or ''
                        display_name = f"{first} {last}".strip() or "Unknown"

                    # Reply Info
                    reply_info = None
                    if message.is_reply:
                        r_id = message.reply_to.reply_to_msg_id
                        if chat_username:
                            link = f"https://t.me/{chat_username}/{r_id}"
                        else:
                            clean_chat_id = str(chat.id).replace("-100", "")
                            link = f"https://t.me/c/{clean_chat_id}/{r_id}"
                        reply_info = f"MsgID:{r_id} Link:{link}"

                    # Content
                    text = message.text or ""
                    if not text and message.media:
                        text = "<Media Content>"
                    
                    if not text:
                        continue # Пропускаем совсем пустые

                    # Создаем объект модели
                    msg_obj = MessageLog(
                        chat_id=chat.id,
                        chat_title=chat_title,
                        message_id=message.id,
                        date=message.date,  # python datetime объект
                        user_id=user_id,
                        username=username,
                        display_name=display_name,
                        reply_info=reply_info,
                        content=text
                    )

                    batch.append(msg_obj)
                    total_count += 1

                    # --- ЭКОЛОГИЧНАЯ ЗАПИСЬ (BATCH) ---
                    # Пишем в базу каждые 100 сообщений
                    if len(batch) >= 100:
                        db_session.add_all(batch)
                        await db_session.commit()
                        batch = [] # Очищаем список
                        
                    # Логирование и пауза
                    if total_count % 500 == 0:
                        logger.info(f"Сохранено {total_count} сообщений в БД...")
                        await asyncio.sleep(0.5)

                # Записываем остаток, который не вошел в последний батч (меньше 100)
                if batch:
                    db_session.add_all(batch)
                    await db_session.commit()

                logger.info(f"Готово! Всего сохранено в БД: {total_count} сообщений.")

            except FloodWaitError as e:
                logger.warning(f"FloodWait: ждем {e.seconds} сек.")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"Ошибка при записи в БД: {e}", exc_info=True)
                await db_session.rollback() # Откат транзакции при ошибке