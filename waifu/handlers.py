import os
import logging
import asyncio
from telethon import events
from telethon.errors import FloodWaitError

# Настраиваем логирование, чтобы видеть процесс в консоли Docker
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def register_handlers(client):

    @client.on(events.NewMessage(pattern="/ping"))
    async def ping(event):
        await event.reply("pong")

    @client.on(events.ChatAction)
    async def on_added_to_chat(event):
        """
        Срабатывает, когда происходят действия в чате (добавление пользователей, создание и т.д.).
        """
        # Проверяем, что кто-то был добавлен или чат создан
        if not (event.user_added or event.created):
            return

        # Получаем информацию о себе, чтобы проверить, добавили ли НАС
        me = await client.get_me()
        
        # event.users - список пользователей, затронутых событием
        # Если нас нет в этом списке, игнорируем
        if me.id not in [user.id for user in event.users]:
            return

        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', f'Chat_{chat.id}')
        
        logger.info(f"Бот добавлен в чат: {chat_title} (ID: {chat.id}). Начинаю скачивание истории...")

        # Создаем папку для логов, если её нет
        dump_dir = "chat_dumps"
        os.makedirs(dump_dir, exist_ok=True)

        # Формируем имя файла
        # Используем безопасное имя файла, убирая спецсимволы, если нужно, или просто ID
        filename = f"{chat.id}_{chat_title}.txt".replace("/", "_")
        filepath = os.path.join(dump_dir, filename)

        try:
            # Открываем файл для записи
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"--- HISTORY DUMP START: {chat_title} ---\n")
                
                message_count = 0
                
                # reverse=True означает, что мы читаем от старых к новым (хронологически)
                # Это удобнее для чтения лога.
                async for message in client.iter_messages(chat, reverse=True):
                    if message.text:
                        # Форматируем дату
                        date_str = message.date.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Пытаемся получить имя отправителя
                        sender = await message.get_sender()
                        if sender:
                            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'Unknown')
                            if getattr(sender, 'last_name', None):
                                sender_name += f" {sender.last_name}"
                        else:
                            sender_name = "Unknown"

                        # Записываем строку: [Дата] Имя: Текст
                        line = f"[{date_str}] {sender_name}: {message.text}\n"
                        f.write(line)
                        
                        message_count += 1

                        # ЭКОЛОГИЧНОСТЬ:
                        # 1. Сбрасываем буфер записи на диск каждые 100 сообщений, чтобы не занимать память
                        # 2. Логируем прогресс каждые 500 сообщений
                        if message_count % 100 == 0:
                            f.flush()
                        
                        if message_count % 500 == 0:
                            logger.info(f"Скачано {message_count} сообщений из {chat_title}...")
                            # Небольшая пауза, чтобы дать дышать Event Loop'у и не выглядеть как DOS-атака,
                            # хотя Telethon сам обрабатывает FloodWait, это хорошая практика.
                            await asyncio.sleep(0.5)

                f.write(f"\n--- HISTORY DUMP END. Total: {message_count} messages ---\n")
                logger.info(f"Завершено скачивание чата {chat_title}. Сохранено в {filepath}")

        except FloodWaitError as e:
            logger.warning(f"Telegram просит подождать {e.seconds} секунд. Спим...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Ошибка при скачивании чата {chat_title}: {e}")