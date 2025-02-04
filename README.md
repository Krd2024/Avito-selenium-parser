# Тестовое задание для стажера

## Доступ к сервису:
- **UI**: http://127.0.0.1:8000  
- **API-документация (Swagger UI)**: http://127.0.0.1:8000/api/v1docs


## Задача
Необходимо реализовать сервис, позволяющий следить за изменением количества объявлений в **Авито** по определённому **поисковому запросу** и **региону**.

## Требования
- **Язык**: Python  
- **Фреймворк**: FastAPI (или любой другой)  
- **Контейнеризация**: сервис должен запускаться через `docker-compose up`  
- **Код-стайл**: PEP, использование `type hints`, документация к публичным методам  
- **Хранилище данных**:  
  - Внешняя база данных (рекомендуется **MySQL** или **PostgreSQL**)  
  - Запуск базы также должен быть описан в `docker-compose`  
- **Частота обновления данных**: 1 раз в час для каждого `id`  
- **Асинхронная обработка запросов**  

## API Методы
### `POST /add`
- **Описание**: 
    Метод /add принимает поисковую фразу и регион, регистрировать их в системе. Возвращать id этой пары.  
- **Входные данные**:  
  ```json
  {
    "query": "поисковая фраза",
    "region": "название региона"
  }

### `POST /stat`
- **Описание**: 
    Метод /stat Принимает на вход id связки поисковая фраза + регион и интервал, за который нужно вывести счётчики. Возвращает счётчики и соответствующие им временные метки (timestamp).
- **Входные данные**:  
  ```json
  {
  "request_id": 4,
  "start_search": "2025-01-29 12:00",
  "end_search": "2025-01-29 23:59"
    }
- **Ответ**: 
  ```json
  {
    "ads_count": 121261,
    "checked_at": "2025-01-29T20:57:00",
    "request": 4
  },
  {
    "ads_count": 120847,
    "checked_at": "2025-01-29T21:57:00",
    "request": 4
  },
  {
    "ads_count": 120973,
    "checked_at": "2025-01-29T22:57:00",
    "request": 4
  }

## Установка и запуск

### 1. Клонирование репозитория
```sh
git clone https://github.com/Krd2024/Parsing_Avito.git
```

### 2. После установки MySQL выполните команды в MySQL:
```sh
CREATE DATABASE mydatabase;
CREATE USER 'myuser'@'%' IDENTIFIED BY 'mypassword';
GRANT ALL PRIVILEGES ON mydatabase.* TO 'myuser'@'%';
FLUSH PRIVILEGES;
```
### 3. Создайте файл .env в корне проекта:
```sh
NAME=mydatabase
USER=myuser
PASSWORD=mypassword
HOST=localhost
# HOST=db  # Docker
PORT=3306
SECRET_KEY=django-insecure-7+n#n7l84)i1b$!$=j*!284(8nop@7^745l&zrhh+81zsxj%$t
```
### 4. Создайте и активируйте виртуальное окружение:
```sh
python -m venv venv
venv\Scripts\activate   
```
### 5. Установите зависимости:
```sh
pip install -r requirements.txt   
```
### 6. Миграции
```sh
python manage.py migrate   
```
### 7. Запуск проекта
```sh
python manage.py runserver   
```


