from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class RequestUser(models.Model):
    search_phrase = models.CharField(
        max_length=10, blank=True, verbose_name="Фраза для поиска"
    )
    sity = models.CharField(max_length=10, blank=True, verbose_name="Город")

    def __str__(self):
        return f"{self.search_phrase} ({self.city})"


class ResultParsing(models.Model):
    static = models.IntegerField(default=0, verbose_name="Количество объявлений")
    created_ad = models.DateTimeField(auto_now_add=True, verbose_name="Время проверки")
