from django.shortcuts import render
from loguru import logger
from django.shortcuts import render, redirect
from .forms import RequestUserForm

from parsing_app.models import RequestUser, ResultParsing
from parsing_app.services.service import start_search


# Create your views here.
def main(request):
    return render(request, "index.html")


def request_user_view(request):
    if request.method == "POST":
        form = RequestUserForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["search_phrase"]
            sity = form.cleaned_data["sity"]
            # RequestUser.objects.filter(search_phrase=phone, sity=sity).delete() # Очистить записи для связки город + товар

            # Проверить, если такой запрос уже был,использовать его для поиска
            # если не было, создать новый
            data_form, created = RequestUser.objects.get_or_create(
                search_phrase=phone, sity=sity
            )
            data_search = data_form if data_form else created

            # Передаёт объект поиска (что искать,город ,ID поиска) в сервис
            # сервис запускает планировщик с поиском по параметрам
            start_search(object_search=data_search)
            return redirect("main")
    else:
        form = RequestUserForm()
    return render(request, "request_user_form.html", {"form": form})


def search_view(request):
    if request.method == "POST":
        request_id = request.POST.get("request_id")
        start_data = request.POST.get("start_data")
        stop_data = request.POST.get("stop_data")

        results = ResultParsing.objects.filter(
            request_id=request_id,
            checked_at__gte=start_data,
            checked_at__lte=stop_data,
        ).order_by("checked_at")

        for result in results:
            print(
                f"Поиск: {result.request}\nКоличество: {result.ads_count}\nВремя проверки: {result.checked_at}\n"
            )
        return render(request, "results_parsing.html", {"results": results})
        # return redirect("main")
    return render(request, "results_pars.html")


def list_view(request):
    all_requests = RequestUser.objects.all()
    # for
    return render(request, "all_requests.html", {"requests": all_requests})
