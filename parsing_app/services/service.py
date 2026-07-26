"""Сервисный слой: подготовка данных и запуск планировщика парсинга."""

from typing import Optional

from parsing_app.models import RequestUser
from parsing_app.services.scheduler_ import scheduler_task, sync_selenium_task


def start_search(object_search: Optional[RequestUser] = None) -> None:
    """Формирует данные для скрапинга Авито и ставит задачу в планировщик.

    Запускает асинхронную функцию парсинга по расписанию.

    :param object_search: связка «поисковая фраза + регион», за которой нужно
        следить. Если передан ``None``, ничего не происходит.
    """
    if object_search is None:
        return

    phrase = object_search.search_phrase  # что искать
    city = object_search.sity  # где искать
    search_id = object_search.id  # ID поиска
    url = object_search.url or ""  # полный URL с фильтрами
    price_from = object_search.price_from  # цена от
    price_to = object_search.price_to  # цена до

    # Создать кортеж с фильтрами (расширенный формат)
    data_for_search = (phrase, city, search_id, url, price_from, price_to)

    # Запуск планировщика.
    # sync_selenium_task запускает асинхронную функцию парсинга.
    scheduler_task(sync_selenium_task, data_for_search, str(search_id))


# ----------------------------------------------------------------
