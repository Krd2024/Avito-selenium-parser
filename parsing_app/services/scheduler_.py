from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


def hourly_task():
    print(f"Задача выполняется в {datetime.now()}")


# scheduler = BackgroundScheduler()
# scheduler.add_job(hourly_task, "interval", minutes=1)
# scheduler.start()

# minutes=1
# hours=1
# Остановка планировщика при завершении работы
# import atexit
# atexit.register(lambda: scheduler.shutdown())
