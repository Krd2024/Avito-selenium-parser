# Базовый образ Python
FROM python:3.10-slim

# Не создавать .pyc и не буферизовать вывод (логи видны сразу).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Установка зависимостей для MySQL-клиента и сборки mysqlclient.
# В Debian Bookworm пакета "mysql-client" не существует — сборка падала с
# "Unable to locate package mysql-client". Правильные имена: default-mysql-client
# и default-libmysqlclient-dev (+ pkg-config, без него mysqlclient не собирается).
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Chromium и chromedriver: без браузера Selenium в контейнере не работал вовсе.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Устанавливаем рабочую директорию
WORKDIR /app

# Сначала зависимости — слой кэшируется между сборками.
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта
COPY . .

# Открываем порт для Django (по умолчанию 8000)
EXPOSE 8000

# Команда запуска
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
