from datetime import datetime
from typing import Optional

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_datetime
from loguru import logger

from .forms import RequestUserForm

from parsing_app.models import RequestUser, ResultParsing
from parsing_app.services.service import start_search
from parsing_app.selenium.avito_search import build_search_url

# Форматы, которые присылает <input type="datetime-local"> и обычные формы.
_DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)


def parse_form_datetime(value: Optional[str]) -> Optional[datetime]:
    """Преобразует строку из формы в ``datetime``.

    :param value: значение поля формы (может быть ``None`` или пустым).
    :return: разобранная дата или ``None``, если значение пустое/некорректное.
    """
    if not value:
        return None

    value = value.strip()
    parsed = parse_datetime(value)
    if parsed is not None:
        return parsed

    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


# Create your views here.
def main(request):
    """Главная страница сервиса."""
    return render(request, "index.html")


def request_user_view(request):
    """Принимает запрос на поиск (что искать + город + фильтры)
    Проверяет, есть ли уже такой запрос
    """
    if request.method == "POST":
        form = RequestUserForm(request.POST)
        if form.is_valid():
            phrase = form.cleaned_data["search_phrase"].strip().lower()
            sity = form.cleaned_data["sity"].strip().lower()
            url = (form.cleaned_data.get("url") or "").strip()
            price_from = form.cleaned_data.get("price_from")
            price_to = form.cleaned_data.get("price_to")

            # Проверить, если такой запрос уже был, использовать его для поиска,
            # если не было — создать новый. get_or_create всегда возвращает
            # объект первым элементом, флаг created — второй (раньше здесь была
            # путаница и в сервис мог уйти булев флаг).
            data_search, _created = RequestUser.objects.get_or_create(
                search_phrase=phrase, sity=sity
            )

            # Обновляем фильтры (даже для уже существующего запроса),
            # чтобы пользователь мог менять параметры.
            updated = False
            if data_search.url != url:
                data_search.url = url
                updated = True
            if data_search.price_from != price_from:
                data_search.price_from = price_from
                updated = True
            if data_search.price_to != price_to:
                data_search.price_to = price_to
                updated = True
            if updated:
                data_search.save()

            # Передаёт объект поиска (что искать, город, ID поиска) в сервис,
            # сервис запускает планировщик с поиском по параметрам.
            start_search(object_search=data_search)
            return redirect("list")
    else:
        form = RequestUserForm()
    return render(request, "request_user_form.html", {"form": form})


def search_view(request):
    """Показывает счётчики объявлений за выбранный интервал.

    Пустые или некорректные значения формы больше не приводят к ошибке 500 —
    вместо этого пользователю показывается понятное сообщение.
    
    Поддерживает два действия:
    - search: просто показать результаты для выбранного запроса
    - quick_search: создать/обновить запрос с фильтрами и показать результаты
    """
    all_requests = RequestUser.objects.all().order_by("id")

    if request.method != "POST":
        return render(
            request, "results_pars.html", {"all_requests": all_requests}
        )

    action = request.POST.get("action", "search")
    
    # Быстрый поиск: создаём/обновляем запрос с фильтрами
    if action == "quick_search":
        search_phrase = (request.POST.get("search_phrase") or "").strip().lower()
        sity = (request.POST.get("sity") or "").strip().lower()
        url = (request.POST.get("url") or "").strip()
        price_from_str = (request.POST.get("price_from") or "").strip()
        price_to_str = (request.POST.get("price_to") or "").strip()
        
        errors = []
        if not search_phrase:
            errors.append("Укажите поисковую фразу.")
        if not sity:
            errors.append("Укажите город.")
        
        price_from = None
        price_to = None
        if price_from_str:
            try:
                price_from = int(price_from_str)
            except ValueError:
                errors.append("Некорректная цена 'от'.")
        if price_to_str:
            try:
                price_to = int(price_to_str)
            except ValueError:
                errors.append("Некорректная цена 'до'.")
        
        if price_from is not None and price_to is not None and price_from > price_to:
            errors.append("«Цена от» не может быть больше «цены до».")
        
        if errors:
            return render(
                request,
                "results_pars.html",
                {"errors": errors, "all_requests": all_requests},
                status=400,
            )
        
        # Создаём или обновляем запрос
        data_search, _created = RequestUser.objects.get_or_create(
            search_phrase=search_phrase, sity=sity
        )
        
        # Обновляем фильтры
        updated = False
        if data_search.url != url:
            data_search.url = url
            updated = True
        if data_search.price_from != price_from:
            data_search.price_from = price_from
            updated = True
        if data_search.price_to != price_to:
            data_search.price_to = price_to
            updated = True
        if updated:
            data_search.save()
        
        # Запускаем парсинг
        start_search(object_search=data_search)
        
        # Показываем результаты для этого запроса
        results = ResultParsing.objects.filter(request=data_search).order_by("-checked_at")
        
        return render(
            request,
            "results_parsing.html",
            {"results": results, "all_requests": all_requests, "search_url": build_search_url(
                search_phrase, sity, url=url, price_from=price_from, price_to=price_to
            )},
        )
    
    # Обычный поиск: показываем результаты для выбранного запроса
    # Поддержка двух полей: dropdown (request_id) и текстовый ввод (request_id_text).
    # Текстовый ввод имеет приоритет, если заполнен.
    request_id = (request.POST.get("request_id_text") or "").strip()
    if not request_id:
        request_id = (request.POST.get("request_id") or "").strip()
    start_data = parse_form_datetime(request.POST.get("start_data"))
    stop_data = parse_form_datetime(request.POST.get("stop_data"))

    errors = []
    if not request_id.isdigit():
        errors.append("Укажите числовой номер запроса.")
    if request.POST.get("start_data") and start_data is None:
        errors.append("Некорректная дата начала поиска.")
    if request.POST.get("stop_data") and stop_data is None:
        errors.append("Некорректная дата окончания поиска.")
    if start_data and stop_data and stop_data <= start_data:
        errors.append("Дата окончания должна быть позже даты начала.")

    if errors:
        return render(
            request,
            "results_pars.html",
            {"errors": errors, "all_requests": all_requests},
            status=400,
        )

    filters = {"request_id": int(request_id)}
    if start_data:
        filters["checked_at__gte"] = start_data
    if stop_data:
        filters["checked_at__lte"] = stop_data

    results = ResultParsing.objects.filter(**filters).order_by("-checked_at")
    
    # Получаем URL для отображения
    search_url = ""
    try:
        req_obj = RequestUser.objects.get(id=int(request_id))
        search_url = build_search_url(
            req_obj.search_phrase, req_obj.sity,
            url=req_obj.url, price_from=req_obj.price_from, price_to=req_obj.price_to
        )
    except RequestUser.DoesNotExist:
        pass

    for result in results:
        logger.info(
            f"Поиск: {result.request} | Количество: {result.ads_count} "
            f"| Время проверки: {result.checked_at}"
        )
    return render(
        request,
        "results_parsing.html",
        {"results": results, "all_requests": all_requests, "search_url": search_url},
    )


def list_view(request):
    """Список всех зарегистрированных поисковых запросов."""
    all_requests = RequestUser.objects.all().order_by("id")

    return render(request, "all_requests.html", {"requests": all_requests})


def request_results_view(request, request_id):
    """Все результаты для конкретного поискового запроса.

    Доступна по клику на название запроса в списке /list/.
    """
    req = get_object_or_404(RequestUser, pk=request_id)
    results = ResultParsing.objects.filter(request=req).order_by("-checked_at")

    # Строим URL парсинга для отображения
    search_url = build_search_url(
        req.search_phrase, req.sity,
        url=req.url, price_from=req.price_from, price_to=req.price_to
    )

    return render(
        request,
        "request_results.html",
        {"req": req, "results": results, "search_url": search_url},
    )
