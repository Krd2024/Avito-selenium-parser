"""Расширяет поля запроса, нормализует данные и добавляет индексы."""

from django.db import migrations, models


def normalize_and_dedupe(apps, schema_editor):
    """Приводит существующие записи к нижнему регистру и убирает дубли.

    Без этого шага добавление UniqueConstraint падало бы на базах, где уже
    лежат связки вида «Москва» и «москва».
    """
    RequestUser = apps.get_model("parsing_app", "RequestUser")
    ResultParsing = apps.get_model("parsing_app", "ResultParsing")

    seen = {}
    for request_user in RequestUser.objects.all().order_by("id"):
        key = (
            (request_user.search_phrase or "").strip().lower(),
            (request_user.sity or "").strip().lower(),
        )
        if key in seen:
            # Переносим результаты на первую (каноническую) запись и удаляем дубль.
            ResultParsing.objects.filter(request_id=request_user.id).update(
                request_id=seen[key]
            )
            request_user.delete()
            continue

        seen[key] = request_user.id
        if (request_user.search_phrase, request_user.sity) != key:
            request_user.search_phrase, request_user.sity = key
            request_user.save(update_fields=["search_phrase", "sity"])


def noop(apps, schema_editor):
    """Обратная миграция данных не требуется."""


class Migration(migrations.Migration):

    dependencies = [
        ("parsing_app", "0002_alter_resultparsing_checked_at"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="requestuser",
            options={
                "verbose_name": "Поисковый запрос",
                "verbose_name_plural": "Поисковые запросы",
            },
        ),
        migrations.AlterModelOptions(
            name="resultparsing",
            options={
                "ordering": ["checked_at"],
                "verbose_name": "Результат парсинга",
                "verbose_name_plural": "Результаты парсинга",
            },
        ),
        migrations.AlterField(
            model_name="requestuser",
            name="search_phrase",
            field=models.CharField(max_length=255, verbose_name="Фраза для поиска"),
        ),
        migrations.AlterField(
            model_name="requestuser",
            name="sity",
            field=models.CharField(max_length=255, verbose_name="Город"),
        ),
        migrations.RunPython(normalize_and_dedupe, noop),
        migrations.AddIndex(
            model_name="resultparsing",
            index=models.Index(
                fields=["request", "checked_at"], name="parsing_app_request_d77385_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="requestuser",
            constraint=models.UniqueConstraint(
                fields=("search_phrase", "sity"), name="unique_search_phrase_sity"
            ),
        ),
    ]
