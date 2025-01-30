# Базовый образ Python
FROM python:3.10
# Установка зависимостей для MySQL-клиента
RUN apt-get update && apt-get install -y mysql-client
# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Открываем порт для Django (по умолчанию 8000)
EXPOSE 8000

# Команда запуска
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
