from parsing_app.services.scheduler_ import scheduler_task, sync_selenium_task


def start_search(object_search=None):
    """Формирует данные для скарпинга Авито."""

    phrase = object_search.search_phrase  # что искать
    city = object_search.sity  # где искать
    search_id = object_search.id  # ID поиска

    # Создать кортеж  (что искать,город ,ID поиска)
    data_for_search = phrase, city, search_id

    # Запуск планировщика
    # sync_selenium_task  Запускает асинхронную функцию
    scheduler_task(sync_selenium_task, data_for_search, str(search_id))

    # logger.info((get_browser, data_for_search, search_id))


# ----------------------------------------------------------------
