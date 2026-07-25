"""Сохранение результатов парсинга в базу данных."""

from typing import Optional

from django.db import close_old_connections
from loguru import logger

from parsing_app.models import RequestUser, ResultParsing


def create_result(data_parsing: dict) -> Optional[ResultParsing]:
    """Сохраняет результат парсинга в БД.

    :param data_parsing: словарь с ключами ``request`` (id связки),
        ``ads_count`` и ``checked_at``.
    :return: созданная запись или ``None``, если сохранить не удалось.
    """
    # Задача выполняется в отдельном потоке планировщика: соединение из пула
    # могло «протухнуть» (MySQL server has gone away) — закрываем устаревшие.
    close_old_connections()

    try:
        request_user = RequestUser.objects.get(id=data_parsing["request"])
        result = ResultParsing.objects.create(
            request=request_user,
            ads_count=data_parsing["ads_count"],
            checked_at=data_parsing["checked_at"],
        )

        logger.info(
            f"Сохранён результат для: {result.request}. "
            f"Объявлений: {result.ads_count} время проверки: {result.checked_at}"
        )
        return result

    except RequestUser.DoesNotExist:
        logger.error(f"Запрос с id={data_parsing.get('request')} не найден в БД.")
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Ошибка - {exc}")
        return None
    finally:
        close_old_connections()
