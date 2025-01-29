from datetime import datetime
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
    checked_at = models.DateTimeField(verbose_name="Время проверки")

    def save(self, *args, **kwargs):
        # Округляем время до минут
        if self.checked_at:
            self.checked_at = self.checked_at.replace(second=0, microsecond=0)
        else:
            # Если checked_at не задано, установим текущее время
            self.checked_at = datetime.now().replace(second=0, microsecond=0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Результат для {self.request} (объявлений: {self.ads_count} время:{self.checked_at})"
