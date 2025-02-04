from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger
import asyncio
import atexit

from parsing_app.selenium.avito_search import selenium_task

# Создаёт ThreadPoolExecutor с 10 потоками
executors = {"default": ThreadPoolExecutor(10)}

# Глобальный планировщик
scheduler = BackgroundScheduler(executors=executors)


def sync_selenium_task(data):
    """Запускает асинхронную функцию в синхронном APScheduler"""

    loop = asyncio.new_event_loop()  # Создаем новый event loop для потока
    asyncio.set_event_loop(loop)
    loop.run_until_complete(selenium_task(data))
    loop.close()


def start_scheduler():
    """Запускает глобальный планировщик."""

    try:
        scheduler.start()
        logger.info("Планировщик запущен.")
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {e}")


def stop_scheduler():
    """Останавливает глобальный планировщик."""

    try:
        scheduler.shutdown()
        logger.info("Планировщик остановлен.")
    except Exception as e:
        logger.error(f"Ошибка при остановке планировщика: {e}")


# Регистрируем остановку планировщика при завершении программы
atexit.register(stop_scheduler)


def scheduler_task(task, data_for_search, task_id, minutes=5):
    """
    Добавляет задачу в глобальный планировщик.

    :param task: Функция, которая будет выполняться.
    :param task_id: Уникальный идентификатор задачи (строка).
    :param minutes: Интервал выполнения задачи в минутах.
    """
    logger.info(data_for_search)

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
            max_instances=5,
        )
        logger.info(f"Задача '{task_id}' добавлена в планировщик.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи '{task_id}': {e}")


# Запускаем планировщик при импорте модуля
start_scheduler()

# =================================================================

# При использовании триггера "interval" вы можете указать следующие параметры:

# seconds: Интервал в секундах.

# minutes: Интервал в минутах.

# hours: Интервал в часах.

# days: Интервал в днях.

# start_date: Дата и время, когда задача должна начать выполняться (по умолчанию — сразу).

# end_date: Дата и время, когда задача должна перестать выполняться.

# timezone: Часовой пояс для выполнения задачи.
