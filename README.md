# Тестовое задание для стажера

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
-----
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

### Вариант 0. Windows: один .exe без установки Python

Проект собирается в единственный файл `AvitoParser.exe`, который запускается
двойным кликом на любой Windows 10/11 x64: он сам применяет миграции,
поднимает локальный сервер и открывает интерфейс в браузере.

```bat
windows\build_exe.bat        :: сборка на Windows → dist\AvitoParser.exe
```

Собрать можно и без Windows-машины — в GitHub Actions: готовый workflow
лежит в `windows/github-workflow-build-windows-exe.yml`, скопируйте его
в `.github/workflows/` (см. инструкцию ниже).

Условие: на компьютере пользователя должен быть установлен **Google Chrome**
(парсер управляет настоящим браузером). Драйвер скачивается автоматически.

Подробности, настройки и разбор проблем — в [`windows/README.md`](windows/README.md).

### Вариант 1. Docker (рекомендуется)
```sh
git clone https://github.com/Krd2024/Avito-selenium-parser.git
cd Avito-selenium-parser
docker compose up --build
```
Все переменные окружения уже заданы в `docker-compose.yml`, отдельный `.env`
для этого варианта не нужен. MySQL поднимается тем же compose-файлом, а
приложение дожидается его готовности (healthcheck) и само применяет миграции.

### Вариант 2. Локальный запуск

#### 1. Клонирование репозитория
```sh
git clone https://github.com/Krd2024/Avito-selenium-parser.git
cd Avito-selenium-parser
```

#### 2. Создайте файл `.env` (за основу возьмите `.env.example`)
```sh
cp .env.example .env
```
По умолчанию используется SQLite — проект запускается сразу, без установки
MySQL. Чтобы переключиться на MySQL, укажите в `.env`:
```sh
DB_ENGINE=mysql
```
и создайте базу и пользователя:
```sql
CREATE DATABASE mydatabase;
CREATE USER 'myuser'@'%' IDENTIFIED BY 'mypassword';
GRANT ALL PRIVILEGES ON mydatabase.* TO 'myuser'@'%';
FLUSH PRIVILEGES;
```

#### 3. Создайте и активируйте виртуальное окружение
```sh
python -m venv venv
source venv/bin/activate     # Linux / macOS
venv\Scripts\activate        # Windows
```

#### 4. Установите зависимости
```sh
pip install -r requirements.txt
```

#### 5. Миграции
```sh
python manage.py migrate
```

#### 6. Запуск проекта
```sh
python manage.py runserver
```

## Тесты
```sh
RUN_SCHEDULER=False python manage.py test parsing_app
```

## Переменные окружения
| Переменная | По умолчанию | Описание |
|---|---|---|
| `SECRET_KEY` | dev-ключ | Секретный ключ Django (обязателен в проде) |
| `DEBUG` | `True` | Режим отладки |
| `ALLOWED_HOSTS` | `*` | Список хостов через запятую |
| `DB_ENGINE` | `sqlite` | `sqlite` (локально) или `mysql` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | см. `.env.example` | Параметры БД |
| `PARSE_INTERVAL_MINUTES` (или `PERIOD`) | `60` | Периодичность опроса Авито, мин. |
| `RUN_SCHEDULER` | `True` | Восстанавливать задачи парсинга при старте |
| `PROXY_FILE` | `proxies.txt` | Файл со списком прокси (формат в `proxies.txt.example`) |
| `PROXY_LIST` | пусто | Прокси через запятую прямо в окружении |
| `PROXY_ROTATION` | `round_robin` | Ротация прокси: `round_robin` или `random` |
| `PROXY_MAX_FAILURES` | `3` | Сбоев до временного исключения прокси |
| `PROXY_COOLDOWN_MINUTES` | `30` | Время исключения сбойного прокси, мин. |
| `PARSE_PROXY_ATTEMPTS` | `3` | Сколько прокси перебрать на задачу при блокировках |

## Прокси и ротация (обход блокировок)

Авито быстро банит IP парсера, поэтому поддерживается пул прокси с ротацией:

1. Создайте файл прокси:
   ```sh
   cp proxies.txt.example proxies.txt
   ```
   и впишите свои прокси (по одному на строку). Поддерживаются форматы
   `host:port`, `host:port:login:password`, `login:password@host:port`,
   `http://…`, `socks5://…`. Вместо файла можно задать `PROXY_LIST` в `.env`.
2. Каждый запуск браузера идёт через следующий прокси по кругу
   (`PROXY_ROTATION=random` — в случайном порядке).
3. Если Авито показывает капчу/блокировку или прокси сбоит, парсер
   автоматически повторяет запрос со следующим прокси
   (`PARSE_PROXY_ATTEMPTS` попыток на задачу).
4. Прокси с капчей банится сразу, просто сбойный — после
   `PROXY_MAX_FAILURES` сбоев; бан длится `PROXY_COOLDOWN_MINUTES`,
   затем прокси возвращается в ротацию.
5. Если список прокси пуст — парсер работает напрямую, как раньше.

`proxies.txt` добавлен в `.gitignore` (может содержать пароли).
Рекомендуются residential/мобильные прокси РФ — датацентровые Авито банит
быстрее.

## Доступ к сервису:
- **UI**: http://127.0.0.1:8000  
- **API-документация (Swagger UI)**: http://127.0.0.1:8000/api/v1/docs/


                                          
![4_ Avito Parsing — Яндекс Браузер 04 02 2025 17_08_47](https://github.com/user-attachments/assets/208c370d-b5ea-437c-9b33-b57010521911)

![result_4_ Avito Parsing — Яндекс Браузер 04 02 2025 17_32_37](https://github.com/user-attachments/assets/4844934f-06d2-4f7f-be11-67028cbb70fc)


![4_ Swagger — Яндекс Браузер 04 02 2025 19_28_25](https://github.com/user-attachments/assets/43d1b95b-a5f0-46f6-a368-62698972aa2f)




## Локальный десктопный запуск (без Docker и runserver)

`run_app.py` — та же точка входа, что используется в .exe: миграции,
production-сервер waitress и открытие браузера.

```sh
pip install -r requirements.txt -r windows/requirements-build.txt
python run_app.py                 # http://127.0.0.1:8000
python run_app.py --port 8100 --no-browser
```
