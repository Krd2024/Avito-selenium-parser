# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parsing_app", "0004_requestuser_url_and_price_filters"),
    ]

    operations = [
        migrations.AddField(
            model_name="requestuser",
            name="local_priority",
            field=models.BooleanField(
                default=False,
                help_text="Включить переключатель 'Сначала из города' на Avito. "
                "Показывает объявления только из указанного города.",
                verbose_name="Сначала из города",
            ),
        ),
    ]
