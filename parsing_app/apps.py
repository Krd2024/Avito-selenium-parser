"""Конфигурация приложения parsing_app."""

import os
import sys

from django.apps import AppConfig


class ParsingAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "parsing_app"
    verbose_name = "Парсинг Авито"

    def ready(self) -> None:
        """Восстанавливает задачи парсинга после старта веб-сервера.

        Планировщик хранит задачи в памяти, поэтому без восстановления
        перезапуск сервиса останавливал опрос всех ранее созданных связок.
        Задачи не поднимаются во время management-команд (``migrate``,
        ``test``, ``collectstatic``, ...) и в перезагрузчике runserver.
        """
        management_command = sys.argv[1] if len(sys.argv) > 1 else ""
        if management_command and management_command not in ("runserver",):
            return

        # runserver поднимает два процесса; задачи нужны только в рабочем.
        if management_command == "runserver" and os.environ.get("RUN_MAIN") != "true":
            return

        from django.conf import settings

        if not getattr(settings, "RUN_SCHEDULER", True):
            return

        # Запрос к БД прямо в ready() вызывает RuntimeWarning
        # («Accessing the database during app initialization»), поэтому
        # восстановление откладывается до полной загрузки приложений.
        from django.core.signals import request_started
        from django.dispatch import receiver

        @receiver(request_started, weak=False, dispatch_uid="parsing_app.restore_jobs")
        def _restore_once(sender, **kwargs) -> None:
            """Восстанавливает задачи при первом входящем запросе."""
            request_started.disconnect(dispatch_uid="parsing_app.restore_jobs")

            from parsing_app.services.scheduler_ import restore_jobs

            restore_jobs()
