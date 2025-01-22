from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Отключаем логирование APScheduler
# logging.getLogger("apscheduler").setLevel(logging.WARNING)

# Глобальный планировщик
scheduler = BackgroundScheduler()


def start_scheduler():
    """
    Запускает глобальный планировщик.
    """
    try:
        scheduler.start()
        logger.info("Планировщик запущен.")
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {e}")


def stop_scheduler():
    """
    Останавливает глобальный планировщик.
    """
    try:
        scheduler.shutdown()
        logger.info("Планировщик остановлен.")
    except Exception as e:
        logger.error(f"Ошибка при остановке планировщика: {e}")


# Регистрируем остановку планировщика при завершении программы
atexit.register(stop_scheduler)


def scheduler_task(task, task_id, minutes=1):
    """
    Добавляет задачу в глобальный планировщик.

    :param task: Функция, которая будет выполняться.
    :param task_id: Уникальный идентификатор задачи (строка).
    :param minutes: Интервал выполнения задачи в минутах.
    """
    try:
        scheduler.add_job(
            task,
            "interval",
            minutes=minutes,
            id=task_id,  # Уникальный идентификатор задачи
            replace_existing=True,  # Заменить задачу, если она уже существует
        )
        logger.info(f"Задача '{task_id}' добавлена в планировщик.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи '{task_id}': {e}")


# Запускаем планировщик при импорте модуля
start_scheduler()
