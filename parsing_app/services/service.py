from django.shortcuts import get_object_or_404, render
from parsing_app.models import RequestUser
from parsing_app.selenium.avito_search import get_browser
from parsing_app.services.scheduler_ import scheduler_task
from parsing_app.services.tasks import hourly_task


def start_search(object_search):

    phrase = object_search.search_phrase  # что искать
    city = object_search.sity  # где искать
    print(search_id := object_search.id)  # ID поиска

    # Запуск таск для запуска скарпинга с периодом
    scheduler_task(hourly_task, str(search_id))

    # запустить скарпинг авито

    # Get or create RequestUser object
    # request_user, _ = RequestUser.objects.get_or_create(
    #     city=kwargs['city'],
    #     product=kwargs['product'],
    #     start_date=timezone.now(),
    #     end_date=timezone.now() + timezone.timedelta(days=30)
    # )


def search(request_id, start, end):
    # Получаем объект по ID или возвращаем 404, если объект не найден
    obj = get_object_or_404(RequestUser, id=request_id)

    # Узнать кол-во объявлений (город, товар)
    total = get_browser(obj)

    # return render(request, "my_template.html", {"object": obj})
