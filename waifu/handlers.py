import logging
import asyncio
import os
from telethon import events
from telethon.tl.types import User as TlUser, Channel, Chat as TlChat
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload

# Импортируем нашу сессию и модели
from .db import SessionLocal
from .models import MessageLog, User, Chat, UserPic

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

AVATAR_DIR = "session/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def get_or_create_pic(session, client, entity, prefix):
    """
    Скачивает аватарку, сохраняет в userpics и возвращает ID.
    """
    if not hasattr(entity, 'photo') or not entity.photo:
        return None

    photo_id = getattr(entity.photo, 'photo_id', entity.id)
    file_path = os.path.join(AVATAR_DIR, f"{prefix}_{entity.id}_{photo_id}.jpg")

    stmt = select(UserPic).where(UserPic.file_path == file_path)
    result = await session.execute(stmt)
    pic_obj = result.scalar_one_or_none()

    if pic_obj:
        return pic_obj.id

    if not os.path.exists(file_path):
        try:
            await client.download_profile_photo(entity, file=file_path)
        except Exception as e:
            logger.error(f"Failed to download avatar for {entity.id}: {e}")
            return None

    new_pic = UserPic(file_path=file_path)
    session.add(new_pic)
    await session.flush()
    return new_pic.id

async def upsert_user(session, client, sender):
    """
    Создает или обновляет пользователя в БД.
    """
    if not isinstance(sender, TlUser):
        return None

    stmt = select(User).where(User.id == sender.id)
    result = await session.execute(stmt)
    db_user = result.scalar_one_or_none()

    pic_id = await get_or_create_pic(session, client, sender, "user")

    if not db_user:
        db_user = User(
            id=sender.id,
            username=sender.username,
            first_name=sender.first_name,
            last_name=sender.last_name,
            phone=getattr(sender, 'phone', None),
            is_bot=sender.bot,
            avatar_id=pic_id
        )
        session.add(db_user)
    else:
        db_user.username = sender.username
        db_user.first_name = sender.first_name
        db_user.last_name = sender.last_name
        if pic_id: 
            db_user.avatar_id = pic_id
    
    return db_user

async def upsert_chat(session, client, entity):
    """
    Создает или обновляет чат в БД.
    """
    stmt = select(Chat).options(selectinload(Chat.users)).where(Chat.id == entity.id)
    result = await session.execute(stmt)
    db_chat = result.scalar_one_or_none()

    description = None
    pic_id = await get_or_create_pic(session, client, entity, "chat")
    title = getattr(entity, 'title', f'Chat_{entity.id}')
    username = getattr(entity, 'username', None)

    if not db_chat:
        db_chat = Chat(
            id=entity.id,
            title=title,
            username=username,
            description=description,
            avatar_id=pic_id,
            users=[] 
        )
        session.add(db_chat)
    else:
        db_chat.title = title
        db_chat.username = username
        if pic_id:
            db_chat.avatar_id = pic_id
    
    return db_chat


# === ОСНОВНАЯ ЛОГИКА ДАМПА ===

async def start_dump_process(client, chat_entity):
    """
    Запускает процесс сохранения участников и истории чата.
    """
    chat_title = getattr(chat_entity, 'title', f'Chat_{chat_entity.id}')
    logger.info(f"Начинаю работу с чатом: {chat_title}")

    async with SessionLocal() as db_session:
        try:
            # 1. Сохраняем/Обновляем ЧАТ
            db_chat = await upsert_chat(db_session, client, chat_entity)
            await db_session.commit()
            
            processed_users_ids = set()

            # 2. Скачивание всех участников
            logger.info("Скачиваю список всех участников...")
            total_participants = 0
            
            try:
                # iter_participants работает только если мы вступили в чат
                async for participant in client.iter_participants(chat_entity):
                    if participant.id in processed_users_ids:
                        continue

                    user_obj = await upsert_user(db_session, client, participant)
                    await db_session.flush() 

                    if user_obj and user_obj not in db_chat.users:
                        db_chat.users.append(user_obj)
                    
                    processed_users_ids.add(participant.id)
                    total_participants += 1

                    if total_participants % 100 == 0:
                        logger.info(f"Сохранено участников: {total_participants}...")
                        await db_session.commit()
            except Exception as e:
                logger.warning(f"Не удалось скачать список участников (возможно нет прав или это канал): {e}")

            await db_session.commit()
            logger.info(f"Участники обработаны ({total_participants}). Начинаю дамп сообщений...")

            # 3. Дамп сообщений
            batch = []
            total_msg_count = 0

            async for message in client.iter_messages(chat_entity, reverse=True):
                
                sender = await message.get_sender()
                user_db_id = None

                if sender and isinstance(sender, TlUser):
                    if sender.id not in processed_users_ids:
                        user_obj = await upsert_user(db_session, client, sender)
                        await db_session.flush() 
                        
                        if user_obj and user_obj not in db_chat.users:
                            db_chat.users.append(user_obj)
                        
                        processed_users_ids.add(sender.id)
                    user_db_id = sender.id

                reply_info = None
                if message.is_reply:
                    r_id = message.reply_to.reply_to_msg_id
                    chat_uname = getattr(chat_entity, 'username', None)
                    if chat_uname:
                        link = f"https://t.me/{chat_uname}/{r_id}"
                    else:
                        clean_chat_id = str(chat_entity.id).replace("-100", "")
                        link = f"https://t.me/c/{clean_chat_id}/{r_id}"
                    reply_info = f"MsgID:{r_id} Link:{link}"

                text = message.text or ""
                if not text and message.media:
                    text = "<Media Content>"
                
                if not text:
                    continue

                msg_obj = MessageLog(
                    chat_id=chat_entity.id,
                    user_id=user_db_id,
                    message_id=message.id,
                    date=message.date,
                    reply_info=reply_info,
                    content=text
                )

                batch.append(msg_obj)
                total_msg_count += 1

                if len(batch) >= 100:
                    db_session.add_all(batch)
                    await db_session.commit()
                    batch = []
                    
                if total_msg_count % 100 == 0:
                    logger.info(f"Обработано сообщений: {total_msg_count}...")

            if batch:
                db_session.add_all(batch)
                await db_session.commit()

            logger.info(f"Дамп завершен! Сообщений: {total_msg_count}.")

        except FloodWaitError as e:
            logger.warning(f"FloodWait: ждем {e.seconds} сек.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Ошибка при записи в БД: {e}", exc_info=True)
            await db_session.rollback()


# === РЕГИСТРАЦИЯ ХЕНДЛЕРОВ ===

def register_handlers(client):

    @client.on(events.NewMessage(pattern="/ping"))
    async def ping(event):
        await event.reply("pong")
    
    # Регулярка захватывает аргумент после пробела (если есть)
    @client.on(events.NewMessage(pattern=r"/dump(?:\s+(.+))?"))
    async def manual_dump(event):
        # Получаем аргумент (ссылку)
        arg = event.pattern_match.group(1)
        target_entity = None
        
        # 1. Если аргумент есть — пытаемся найти чат по ссылке
        if arg:
            arg = arg.strip()
            await event.reply(f"🔍 Ищу чат по ссылке: {arg}")
            
            try:
                # ОПАСНОСТЬ: Если это приватная ссылка-приглашение (t.me/+...), get_entity не сработает
                if "t.me/+" in arg or "joinchat" in arg:
                    try:
                        # Пытаемся вступить по хэшу
                        hash_arg = arg.split('+')[-1].strip()
                        await client(ImportChatInviteRequest(hash_arg))
                        await event.reply("✅ Успешно вступил по ссылке-приглашению.")
                    except Exception as e:
                        # Если уже вступили, Telethon может кинуть ошибку, но это ок, идем дальше
                        pass
                
                # Теперь пытаемся получить сущность (Telethon сам разберет ссылку, юзернейм или ID)
                target_entity = await client.get_entity(arg)
                
                # Если это публичный чат/канал, но мы не вступили — надо вступить, чтобы скачать историю
                # (Хотя публичные каналы можно читать и так, но для надежности лучше вступить)
                if isinstance(target_entity, (Channel, TlChat)):
                     # Проверка membership (упрощенная) - просто пробуем Join, если не выйдет - не страшно
                     try:
                         await client(JoinChannelRequest(target_entity))
                     except:
                         pass

            except Exception as e:
                await event.reply(f"❌ Ошибка поиска чата: {e}\nУбедись, что ссылка корректная и бот не забанен.")
                return

        # 2. Если аргумента нет...
        else:
            if event.is_private:
                # В личке без ссылки нельзя
                await event.reply("ℹ️ В личных сообщениях нужно указать ссылку:\n`/dump https://t.me/username`")
                return
            else:
                # В группе без ссылки — дампим текущую группу
                target_entity = await event.get_chat()

        # Защита от дурака: не дампить личку
        if isinstance(target_entity, TlUser):
            await event.reply("⛔️ Нельзя дампить личную переписку по ссылке (только группы/каналы).")
            return

        # Запуск процесса
        chat_title = getattr(target_entity, 'title', f"Chat {target_entity.id}")
        await event.reply(f"🚀 Начинаю дамп чата: **{chat_title}**\nСледи за логами.")
        
        # Запускаем в фоне, чтобы не блокировать бота (хотя здесь await заблокирует этот хендлер, но другие будут работать)
        await start_dump_process(client, target_entity)
        await event.reply(f"🏁 Дамп чата **{chat_title}** завершен!")

    @client.on(events.ChatAction)
    async def on_added_to_chat(event):
        # Автоматика при добавлении
        is_enter_event = (event.user_added or event.user_joined or event.created)
        me = await client.get_me()
        
        if not is_enter_event:
            if not (event.user_ids and me.id in event.user_ids):
                return
        if event.user_ids and me.id not in event.user_ids:
             return

        logger.info("Обнаружено вступление в чат. Ожидание 5 сек...")
        await asyncio.sleep(5)

        try:
            chat_entity = await client.get_entity(event.chat_id)
            await start_dump_process(client, chat_entity)
        except Exception as e:
            logger.error(f"Ошибка при авто-дампе: {e}")