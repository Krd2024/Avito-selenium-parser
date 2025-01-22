from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler

from parsing_app.services.scheduler_ import hourly_task

scheduler = BackgroundScheduler()


class ParsingAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "parsing_app"

    def ready(self):
        scheduler.add_job(hourly_task, "interval", minutes=1)
        scheduler.start()
