"""Тесты сервиса отслеживания количества объявлений на Авито."""

from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from parsing_app.models import RequestUser, ResultParsing
from parsing_app.selenium.avito_search import build_search_url, parse_ads_count
from parsing_app.selenium.db import create_result
from parsing_app.views import parse_form_datetime


class ParseAdsCountTests(TestCase):
    """Разбор счётчика объявлений со страницы Авито."""

    def test_plain_number(self):
        self.assertEqual(parse_ads_count("5 объявлений"), 5)

    def test_regular_space_separator(self):
        self.assertEqual(parse_ads_count("12 345 объявлений"), 12345)

    def test_other_word_form(self):
        """Старый код падал на окончании «объявление»."""
        self.assertEqual(parse_ads_count("121 261 объявление"), 121261)

    def test_non_breaking_space(self):
        """Авито разделяет разряды неразрывным пробелом."""
        self.assertEqual(parse_ads_count("1\u00a0234 объявления"), 1234)
        self.assertEqual(parse_ads_count("121\u202f261 объявлений"), 121261)

    def test_no_digits(self):
        self.assertIsNone(parse_ads_count("Ничего не найдено"))
        self.assertIsNone(parse_ads_count(""))


class BuildSearchUrlTests(TestCase):
    """Формирование прямой ссылки на поиск."""

    def test_url_contains_city_and_query(self):
        url = build_search_url("ноутбук", "краснодар")
        self.assertTrue(url.startswith("https://www.avito.ru/"))
        self.assertIn("q=", url)
        # Город должен быть транслитерирован в латиницу, а не закодирован кириллицей
        self.assertIn("/krasnodar?", url)
        path = url.split("?")[0]
        self.assertNotIn("%D0", path)
        self.assertNotIn("%d0", path.lower())

    def test_multiword_city_is_slugified(self):
        """Пробелы в названии города не должны попадать в URL."""
        url = build_search_url("стол", "нижний новгород")
        self.assertNotIn(" ", url)
        # Авито использует дефис: sankt-peterburg, nizhniy-novgorod
        self.assertIn("nizhniy-novgorod", url)
        self.assertNotIn("_", url)

    def test_moscow_slug(self):
        url = build_search_url("телефон", "Москва")
        self.assertIn("/moskva?", url)

    def test_empty_city_falls_back_to_all(self):
        self.assertIn("/all", build_search_url("стол", ""))

    def test_real_avito_url_format(self):
        """Итоговый URL должен соответствовать реальному формату Авито."""
        url = build_search_url("телефон", "Москва")
        # Пример реального: https://www.avito.ru/moskva?q=телефон
        self.assertRegex(url, r"^https://www\.avito\.ru/[a-z0-9-]+\?q=.+")
        self.assertIn("q=", url)


class ParseFormDatetimeTests(TestCase):
    """Разбор значений из HTML-формы."""

    def test_datetime_local_format(self):
        self.assertEqual(
            parse_form_datetime("2025-06-01T10:30"), datetime(2025, 6, 1, 10, 30)
        )

    def test_space_separated_format(self):
        self.assertEqual(
            parse_form_datetime("2025-06-01 10:30"), datetime(2025, 6, 1, 10, 30)
        )

    def test_empty_and_invalid(self):
        self.assertIsNone(parse_form_datetime(""))
        self.assertIsNone(parse_form_datetime(None))
        self.assertIsNone(parse_form_datetime("не дата"))


class ModelTests(TestCase):
    """Поведение моделей."""

    def test_long_search_phrase_is_allowed(self):
        """Раньше max_length=10 не давал сохранить обычный запрос."""
        obj = RequestUser.objects.create(
            search_phrase="iphone 15 pro max 256gb",
            sity="санкт-петербург",
        )
        obj.full_clean()  # не должно бросать ValidationError
        self.assertEqual(obj.search_phrase, "iphone 15 pro max 256gb")

    def test_checked_at_is_rounded_to_minutes(self):
        request_user = RequestUser.objects.create(search_phrase="стол", sity="москва")
        result = ResultParsing.objects.create(
            request=request_user,
            ads_count=10,
            checked_at=datetime(2025, 6, 1, 10, 30, 45, 123456),
        )
        result.refresh_from_db()
        self.assertEqual(result.checked_at.second, 0)
        self.assertEqual(result.checked_at.microsecond, 0)

    def test_checked_at_defaults_to_now(self):
        request_user = RequestUser.objects.create(search_phrase="стул", sity="москва")
        result = ResultParsing(request=request_user, ads_count=1)
        result.save()
        self.assertIsNotNone(result.checked_at)


class CreateResultTests(TestCase):
    """Запись результатов парсинга в БД."""

    def test_saves_result(self):
        request_user = RequestUser.objects.create(search_phrase="диван", sity="москва")
        result = create_result(
            {
                "request": request_user.id,
                "ads_count": 42,
                "checked_at": datetime(2025, 6, 1, 12, 0),
            }
        )
        self.assertIsNotNone(result)
        self.assertEqual(ResultParsing.objects.count(), 1)

    def test_unknown_request_does_not_raise(self):
        """Отсутствующий id не должен ронять поток планировщика."""
        self.assertIsNone(
            create_result(
                {"request": 999999, "ads_count": 1, "checked_at": datetime.now()}
            )
        )


@mock.patch("parsing_app.drf.views_drf.start_search")
class AddApiTests(TestCase):
    """Метод POST /api/v1/add/."""

    url = "/api/v1/add/"

    def test_creates_pair_and_returns_id(self, mocked_start):
        response = self.client.post(
            self.url,
            data={"search_phrase": "Ноутбук", "sity": "Москва"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())
        # Значения нормализуются к нижнему регистру.
        self.assertEqual(RequestUser.objects.get().search_phrase, "ноутбук")
        mocked_start.assert_called_once()

    def test_same_pair_returns_same_id(self, mocked_start):
        first = self.client.post(
            self.url,
            data={"search_phrase": "ноутбук", "sity": "москва"},
            content_type="application/json",
        ).json()
        second = self.client.post(
            self.url,
            data={"search_phrase": "Ноутбук", "sity": "МОСКВА"},
            content_type="application/json",
        ).json()
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(RequestUser.objects.count(), 1)

    def test_long_values_are_accepted(self, mocked_start):
        """Регресс: max_length=10 отклонял «Санкт-Петербург»."""
        response = self.client.post(
            self.url,
            data={"search_phrase": "iphone 15 pro max", "sity": "Санкт-Петербург"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_missing_field_returns_400_not_500(self, mocked_start):
        """Регресс: отсутствующий sity вызывал AttributeError (500)."""
        response = self.client.post(
            self.url,
            data={"search_phrase": "ноутбук"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("sity", response.json())

    def test_blank_values_rejected(self, mocked_start):
        response = self.client.post(
            self.url,
            data={"search_phrase": "", "sity": ""},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class StatApiTests(TestCase):
    """Метод POST /api/v1/stat/."""

    url = "/api/v1/stat/"

    def setUp(self):
        self.request_user = RequestUser.objects.create(
            search_phrase="ноутбук", sity="москва"
        )
        for hour, count in ((20, 121261), (21, 120847), (22, 120973)):
            ResultParsing.objects.create(
                request=self.request_user,
                ads_count=count,
                checked_at=datetime(2025, 1, 29, hour, 57),
            )

    def test_returns_counters_in_interval(self):
        response = self.client.post(
            self.url,
            data={
                "request_id": self.request_user.id,
                "start_search": "2025-01-29 12:00",
                "end_search": "2025-01-29 23:59",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload[0]["ads_count"], 121261)
        self.assertEqual(payload[0]["request"], self.request_user.id)

    def test_interval_filters_results(self):
        response = self.client.post(
            self.url,
            data={
                "request_id": self.request_user.id,
                "start_search": "2025-01-29 21:00",
                "end_search": "2025-01-29 21:59",
            },
            content_type="application/json",
        )
        self.assertEqual(len(response.json()), 1)

    def test_end_before_start_rejected(self):
        response = self.client.post(
            self.url,
            data={
                "request_id": self.request_user.id,
                "start_search": "2025-01-29 23:00",
                "end_search": "2025-01-29 12:00",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_id_returns_404(self):
        response = self.client.post(
            self.url,
            data={
                "request_id": 999999,
                "start_search": "2025-01-01 00:00",
                "end_search": "2026-01-01 00:00",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


@mock.patch("parsing_app.views.start_search")
class UiViewTests(TestCase):
    """HTML-интерфейс."""

    def test_pages_render(self, mocked_start):
        for name in ("main", "request_user_vies", "search", "list"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_create_form_registers_request(self, mocked_start):
        response = self.client.post(
            reverse("request_user_vies"),
            data={"search_phrase": "Стол", "sity": "Москва"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RequestUser.objects.count(), 1)
        mocked_start.assert_called_once()
        # В сервис должен уходить объект, а не булев флаг created.
        self.assertIsInstance(
            mocked_start.call_args.kwargs["object_search"], RequestUser
        )

    def test_search_shows_results(self, mocked_start):
        request_user = RequestUser.objects.create(
            search_phrase="стол", sity="москва"
        )
        ResultParsing.objects.create(
            request=request_user, ads_count=100, checked_at=datetime(2025, 6, 1, 10, 30)
        )
        response = self.client.post(
            reverse("search"),
            data={
                "request_id": str(request_user.id),
                "start_data": "2025-06-01T00:00",
                "stop_data": "2025-06-02T00:00",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100")

    def test_empty_form_does_not_crash(self, mocked_start):
        """Регресс: пустые поля вызывали ValidationError и ошибку 500."""
        response = self.client.post(
            reverse("search"),
            data={"request_id": "", "start_data": "", "stop_data": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response, "Укажите числовой номер запроса", status_code=400
        )

    def test_invalid_dates_reported(self, mocked_start):
        response = self.client.post(
            reverse("search"),
            data={"request_id": "1", "start_data": "abc", "stop_data": "xyz"},
        )
        self.assertEqual(response.status_code, 400)


class SchedulerTests(TestCase):
    """Планировщик периодических задач."""

    def test_job_registered_with_hourly_interval_and_immediate_first_run(self):
        from parsing_app.services.scheduler_ import scheduler, scheduler_task

        executed = []
        job_id = "test-job"
        try:
            scheduler_task(
                lambda data: executed.append(data),
                ("ноутбук", "москва", 1),
                job_id,
                run_now=True,
            )
            job = scheduler.get_job(f"task_{job_id}")
            self.assertIsNotNone(job)
            self.assertEqual(job.trigger.interval.total_seconds(), 3600)
            # Регресс: раньше первый запуск планировался только через час.
            self.assertIsNotNone(job.next_run_time)
        finally:
            if scheduler.get_job(f"task_{job_id}"):
                scheduler.remove_job(f"task_{job_id}")

    def test_start_search_ignores_none(self):
        from parsing_app.services.service import start_search

        start_search(None)  # не должно бросать исключение

    def test_sync_selenium_task_survives_errors(self):
        from parsing_app.services import scheduler_

        with mock.patch.object(
            scheduler_, "selenium_task", side_effect=RuntimeError("boom")
        ):
            # Исключение внутри задачи не должно ронять поток планировщика.
            scheduler_.sync_selenium_task(("a", "b", 1))
