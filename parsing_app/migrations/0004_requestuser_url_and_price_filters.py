"""Добавляет поля фильтров: url, price_from, price_to."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parsing_app", "0003_normalize_requests_and_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="requestuser",
            name="url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Полная ссылка на поиск Avito с нужными фильтрами. "
                "Если указана — используется вместо автоматической сборки URL.",
                max_length=2048,
                verbose_name="URL с фильтрами",
            ),
        ),
        migrations.AddField(
            model_name="requestuser",
            name="price_from",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Цена от"
            ),
        ),
        migrations.AddField(
            model_name="requestuser",
            name="price_to",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Цена до"
            ),
        ),
    ]
