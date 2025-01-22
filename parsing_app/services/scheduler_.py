from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime


# Глобальный планировщик
scheduler = BackgroundScheduler()

# Запуск планировщика
scheduler.start()


# Остановка планировщика при завершении работы
atexit.register(lambda: scheduler.shutdown())


def scheduler_task(task, task_id, minutes=1):
    """
    Добавляет задачу в глобальный планировщик.

    :param task: Функция, которая будет выполняться.
    :param task_id: Уникальный идентификатор задачи.
    :param minutes: Интервал выполнения задачи в минутах.
    """
    scheduler.add_job(
        task,
        "interval",
        minutes=minutes,
        id=task_id,  # Уникальный идентификатор задачи
        replace_existing=True,  # Заменить задачу, если она уже существует
    )
