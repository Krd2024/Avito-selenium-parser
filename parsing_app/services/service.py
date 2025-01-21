from django.shortcuts import get_object_or_404, render

from parsing_app.models import RequestUser


def search(request_id, start, end):
    # Получаем объект по ID или возвращаем 404, если объект не найден
    obj = get_object_or_404(RequestUser, id=request_id)
    print(obj)
    print(start, end)

    # return render(request, "my_template.html", {"object": obj})
