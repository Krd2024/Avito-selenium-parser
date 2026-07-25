# Базовый образ Python
FROM python:3.12-slim

# Не создавать .pyc и не буферизовать вывод (логи видны сразу).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем зависимости для сборки mysqlclient и клиент MySQL.
# Важно: пакета "mysql-client" в Debian нет — сборка падала с
# "Unable to locate package mysql-client". Правильное имя — default-mysql-client.
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    default-libmysqlclient-dev \
    default-mysql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Chromium и chromedriver: без браузера Selenium в контейнере не работал вовсе.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

# Сначала зависимости — слой кэшируется между сборками.
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта
COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
