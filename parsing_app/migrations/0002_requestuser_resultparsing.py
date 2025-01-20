# Generated by Django 5.1.5 on 2025-01-20 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search_phrase', models.CharField(blank=True, max_length=10, verbose_name='Фраза для поиска')),
                ('sity', models.CharField(blank=True, max_length=10, verbose_name='Город')),
            ],
        ),
        migrations.CreateModel(
            name='ResultParsing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('static', models.IntegerField(default=0, verbose_name='Количество объявлений')),
                ('created_ad', models.DateTimeField(auto_now_add=True, verbose_name='Время проверки')),
            ],
        ),
    ]
