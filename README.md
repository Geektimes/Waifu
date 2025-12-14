-=Waifu=- --- Telegram Userbot
![alt text](https://img.shields.io/badge/Python-3.13-blue?logo=python)

![alt text](https://img.shields.io/badge/Telethon-Async-orange)

![alt text](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)

![alt text](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
🇷🇺 Русский | 🇺🇸 English
🇷🇺 Russian
Waifu Userbot — это асинхронный юзербот для Telegram, предназначенный для создания дампов (резервных копий) истории чатов. Он сохраняет сообщения, информацию о пользователях, чатах и скачивает аватарки в локальную базу данных PostgreSQL.
✨ Возможности
Сохранение истории: Скачивает сообщения из групп, супергрупп, каналов и личных переписок.
База пользователей: Сохраняет всех участников чата, даже если они не писали сообщений (используется iter_participants).
Аватарки: Скачивает аватарки пользователей и чатов в папку session/avatars и привязывает их в БД.
Умный дамп:
Автоматически: При вступлении в новый чат.
Вручную: Команда /dump для текущего чата.
По ссылке: /dump https://t.me/username (работает даже в ЛС).
PostgreSQL: Использование мощной реляционной БД с ORM SQLAlchemy (Async).
Docker: Полная изоляция и простой запуск.
🛠 Установка и запуск
1. Предварительные требования
Установленные Docker и Docker Compose.
Полученные API_ID и API_HASH на сайте my.telegram.org.
2. Клонирование и настройка
Скопируйте проект и создайте файл .env в корневой папке:
code
Bash
# .env
API_ID=1234567
API_HASH=ващ_хэш_тут
3. Первый запуск (Авторизация)
При первом запуске нужно ввести номер телефона и код подтверждения. Так как Docker запускается в фоне, первый раз запустим его интерактивно:
code
Bash
# Сборка контейнера
docker-compose build

# Запуск для авторизации (следуйте инструкциям в терминале)
docker-compose run --rm waifu
После успешного входа создастся файл сессии в папке session/. Нажмите Ctrl+C, чтобы выйти.
4. Запуск в фоне
Теперь можно запустить бота в рабочем режиме:
code
Bash
docker-compose up -d
🎮 Использование (Команды)
Отправляйте эти команды с аккаунта, на котором запущен юзербот (или в «Избранное»).
Команда	Описание
/ping	Проверка работоспособности (ответ pong).
/dump	Полный дамп текущего чата/группы (сообщения + участники).
/dump <ссылка>	Дамп чата по ссылке или ID. <br>Пример: /dump https://t.me/durov или /dump @username.<br>Работает даже из Личных Сообщений.
/export_db	(Опционально) Создает .sql дамп базы данных и присылает файл в чат.
📂 Структура данных
PostgreSQL: Доступна на порту 5432 (если проброшен в docker-compose).
chats — информация о группах/каналах.
users — информация о пользователях.
messages — история сообщений.
userpics — пути к файлам аватарок.
Файлы: Аватарки сохраняются в папку проекта: ./session/avatars/.
🇺🇸 English
Waifu Userbot is an asynchronous Telegram userbot designed to dump (backup) chat history. It saves messages, user info, chat metadata, and downloads avatars into a local PostgreSQL database.
✨ Features
History Backup: Downloads messages from groups, supergroups, channels, and private chats.
User Database: Saves all chat participants, even silent ones (using iter_participants).
Avatars: Downloads user and chat profile pictures to session/avatars and links them in the DB.
Smart Dump:
Automatic: Triggers when joining a new chat.
Manual: Command /dump for the current chat.
By Link: /dump https://t.me/username (works even from Private Messages).
PostgreSQL: Powered by a robust relational DB and SQLAlchemy (Async).
Docker: Fully containerized for easy deployment.
🛠 Installation & Setup
1. Prerequisites
Docker and Docker Compose installed.
API_ID and API_HASH obtained from my.telegram.org.
2. Clone and Configure
Clone the project and create a .env file in the root directory:
code
Bash
# .env
API_ID=1234567
API_HASH=your_hash_here
3. First Run (Login)
On the first run, you need to enter your phone number and 2FA code. Since Docker usually runs in the background, run it interactively for the first time:
code
Bash
# Build the container
docker-compose build

# Run interactively for login (follow the prompts)
docker-compose run --rm waifu
After successful login, a session file will be created in the session/ folder. Press Ctrl+C to exit.
4. Run in Background
Now you can start the bot in production mode:
code
Bash
docker-compose up -d
🎮 Usage (Commands)
Send these commands from the account running the userbot (or to "Saved Messages").
Command	Description
/ping	Health check (replies pong).
/dump	Full dump of the current chat/group (messages + participants).
/dump <link>	Dump a chat by Link or ID. <br>Example: /dump https://t.me/durov or /dump @username.<br>Works from Private Messages.
/export_db	(Optional) Creates a .sql database dump and sends the file to the chat.
📂 Data Structure
PostgreSQL: Accessible via port 5432 (if mapped in docker-compose).
chats — groups/channels metadata.
users — users metadata.
messages — message history.
userpics — paths to avatar files.
Files: Avatars are saved locally in: ./session/avatars/.