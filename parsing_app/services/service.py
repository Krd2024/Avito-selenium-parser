from django.shortcuts import get_object_or_404
from parsing_app.models import RequestUser
from parsing_app.selenium.avito_search import get_browser
from parsing_app.services.scheduler_ import scheduler_task, sync_selenium_task


def start_search(object_search=None):
    """Формирует данные для скарпинга Авито."""

    phrase = object_search.search_phrase  # что искать
    city = object_search.sity  # где искать
    search_id = object_search.id  # ID поиска

    # Создать кортеж  (что искать,город ,ID поиска)
    data_for_search = phrase, city, search_id
    print(data_for_search)

    # Запуск планировщика
    # get_browser = функция скарпинга
    scheduler_task(sync_selenium_task, data_for_search, str(search_id))

    # logger.info((get_browser, data_for_search, search_id))


# ----------------------------------------------------------------
def search(request_id, start, end):
    # Получаем объект по ID или возвращаем 404, если объект не найден
    obj = get_object_or_404(RequestUser, id=request_id)

    # Узнать кол-во объявлений (город, товар)
    get_browser(obj)
