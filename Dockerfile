## Dockerfile
# Используем Python 3.13 slim
FROM python:3.13-slim

# Отключаем буферизацию вывода, чтобы логи были в реальном времени
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Устанавливаем Poetry фиксированной версии
RUN pip install --no-cache-dir poetry==2.1.2

# Копируем файлы зависимостей в контейнер
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости проекта
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Копируем весь код приложения
# Важно: docker-compose монтирует ./waifu:/app, так что изменения в локальной папке
# автоматически отражаются в контейнере
COPY . /app

# Запуск userbot
CMD ["python", "-m", "waifu.main"]
