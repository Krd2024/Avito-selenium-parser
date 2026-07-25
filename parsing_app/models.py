from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    pass


class RequestUser(models.Model):
    """Пара «поисковая фраза + регион», за которой следит сервис."""

    search_phrase = models.CharField(
        max_length=255, verbose_name="Фраза для поиска"
    )
    sity = models.CharField(max_length=255, verbose_name="Город")

    class Meta:
        verbose_name = "Поисковый запрос"
        verbose_name_plural = "Поисковые запросы"
        # Одна и та же связка «фраза + город» не должна дублироваться.
        constraints = [
            models.UniqueConstraint(
                fields=["search_phrase", "sity"], name="unique_search_phrase_sity"
            )
        ]

    def __str__(self) -> str:
        return f"({self.search_phrase}, {self.sity})"


class ResultParsing(models.Model):
    """Снимок количества объявлений для конкретного запроса."""

    request = models.ForeignKey(
        RequestUser, related_name="result_parsing", on_delete=models.CASCADE
    )
    ads_count = models.IntegerField(default=0, verbose_name="Количество объявлений")
    checked_at = models.DateTimeField(verbose_name="Время проверки")

    class Meta:
        verbose_name = "Результат парсинга"
        verbose_name_plural = "Результаты парсинга"
        ordering = ["checked_at"]
        # Ускоряет выборку по /stat (фильтр request_id + диапазон времени).
        indexes = [models.Index(fields=["request", "checked_at"])]

    def save(self, *args, **kwargs) -> None:
        """Округляет время проверки до минут и сохраняет запись."""
        if not self.checked_at:
            # Если checked_at не задано, установим текущее время.
            self.checked_at = timezone.now() if settings.USE_TZ else datetime.now()
        self.checked_at = self.checked_at.replace(second=0, microsecond=0)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"Результат для {self.request} "
            f"(объявлений: {self.ads_count} время:{self.checked_at})"
        )
