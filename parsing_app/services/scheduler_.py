"""Планировщик периодических задач парсинга.

Задачи выполняются раз в час для каждой связки «поисковая фраза + регион».
Планировщик стартует лениво — только когда действительно нужен, — чтобы не
запускаться на каждой management-команде (``migrate``, ``check``, ...).
"""

from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Tuple
import asyncio
import atexit
import threading

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from loguru import logger

from parsing_app.selenium.avito_search import selenium_task

# Создаёт ThreadPoolExecutor с 10 потоками
executors = {"default": ThreadPoolExecutor(10)}

# Глобальный планировщик
scheduler = BackgroundScheduler(executors=executors)

# Защищает ленивый запуск планировщика от гонки между потоками Django.
_scheduler_lock = threading.Lock()


def sync_selenium_task(data: Tuple[str, str, int]) -> None:
    """Запускает асинхронную функцию парсинга в синхронном APScheduler.

    :param data: кортеж «(фраза, город, id связки)».
    """
    loop = asyncio.new_event_loop()  # Создаем новый event loop для потока
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(selenium_task(data))
    except Exception as exc:  # noqa: BLE001 - задача не должна ронять планировщик
        logger.error(f"Ошибка при выполнении задачи парсинга {data}: {exc}")
    finally:
        # Раньше loop.close() не вызывался при исключении — event loop'ы
        # (и их файловые дескрипторы) утекали при каждой ошибке парсинга.
        asyncio.set_event_loop(None)
        loop.close()


def start_scheduler() -> None:
    """Запускает глобальный планировщик, если он ещё не запущен."""
    with _scheduler_lock:
        if scheduler.running:
            return
        try:
            scheduler.start()
            logger.info("Планировщик запущен.")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Ошибка при запуске планировщика: {exc}")


def stop_scheduler() -> None:
    """Останавливает глобальный планировщик, если он работает."""
    if not scheduler.running:
        return
    try:
        scheduler.shutdown(wait=False)
        logger.info("Планировщик остановлен.")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Ошибка при остановке планировщика: {exc}")


# Регистрируем остановку планировщика при завершении программы
atexit.register(stop_scheduler)


def scheduler_task(
    task: Callable[[Any], None],
    data_for_search: Tuple[str, str, int],
    task_id: str,
    minutes: Optional[int] = None,
    run_now: bool = True,
) -> None:
    """
    Добавляет задачу в глобальный планировщик.

    :param task: Функция, которая будет выполняться.
    :param data_for_search: Кортеж «(фраза, город, id связки)».
    :param task_id: Уникальный идентификатор задачи (строка).
    :param minutes: Интервал выполнения задачи в минутах
        (по умолчанию ``settings.PARSE_INTERVAL_MINUTES``, то есть раз в час).
    :param run_now: Выполнить первый замер сразу, не дожидаясь интервала.
    """
    logger.info(data_for_search)

    if minutes is None:
        minutes = getattr(settings, "PARSE_INTERVAL_MINUTES", 60)

    # Планировщик стартует здесь, а не при импорте модуля: так он не
    # поднимается во время `manage.py migrate`/`check` и не висит зря.
    start_scheduler()

    # По умолчанию APScheduler ставит первый запуск через `minutes`, поэтому
    # свежесозданный запрос целый час не имел ни одного результата.
    next_run = datetime.now() + timedelta(seconds=5) if run_now else None

    try:
        scheduler.add_job(
            task,
            "interval",
            minutes=minutes,
            args=[data_for_search],  # ID связки для поиска
            id=f"task_{task_id}",  # Уникальный идентификатор задачи
            replace_existing=True,  # Заменить задачу, если она уже существует
            coalesce=True,
            executor="default",
            max_instances=1,
            misfire_grace_time=300,
            next_run_time=next_run,
        )
        logger.info(f"Задача '{task_id}' добавлена в планировщик.")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Ошибка при добавлении задачи '{task_id}': {exc}")


def restore_jobs() -> None:
    """Восстанавливает задачи для всех сохранённых запросов.

    Планировщик держит задачи в памяти, поэтому после перезапуска сервиса
    ранее зарегистрированные связки переставали опрашиваться. Метод вызывается
    из ``AppConfig.ready()``.
    """
    from parsing_app.models import RequestUser

    try:
        requests = list(RequestUser.objects.all())
    except Exception as exc:  # noqa: BLE001 - БД может быть ещё не мигрирована
        logger.warning(f"Не удалось восстановить задачи планировщика: {exc}")
        return

    for request_user in requests:
        scheduler_task(
            sync_selenium_task,
            (request_user.search_phrase, request_user.sity, request_user.id),
            str(request_user.id),
            run_now=False,
        )
    if requests:
        logger.info(f"Восстановлено задач планировщика: {len(requests)}")


# =================================================================

# При использовании триггера "interval" вы можете указать следующие параметры:

# seconds: Интервал в секундах.

# minutes: Интервал в минутах.

# hours: Интервал в часах.

# days: Интервал в днях.

# start_date: Дата и время, когда задача должна начать выполняться (по умолчанию — сразу).

# end_date: Дата и время, когда задача должна перестать выполняться.

# timezone: Часовой пояс для выполнения задачи.
