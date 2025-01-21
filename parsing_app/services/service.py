from django.shortcuts import get_object_or_404, render

from parsing_app.models import RequestUser
from parsing_app.selenium.avito_search import get_browser


def search(request_id, start, end):
    # Получаем объект по ID или возвращаем 404, если объект не найден
    obj = get_object_or_404(RequestUser, id=request_id)
    # print(obj)
    # print(start, end)
    get_browser(obj)

    # return render(request, "my_template.html", {"object": obj})
