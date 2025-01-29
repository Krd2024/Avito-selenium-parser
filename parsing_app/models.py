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
        return f"({self.search_phrase}, {self.sity})"


class ResultParsing(models.Model):
    request = models.ForeignKey(
        RequestUser, related_name="result_parsing", on_delete=models.CASCADE
    )
    ads_count = models.IntegerField(default=0, verbose_name="Количество объявлений")
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name="Время проверки")

    def __str__(self):
        return f"Результат для {self.request} (объявлений: {self.ads_count} время:{self.checked_at})"
