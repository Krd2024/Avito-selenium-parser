"""Регистрация моделей в админке."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from parsing_app.models import RequestUser, ResultParsing, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админка кастомной модели пользователя."""


@admin.register(RequestUser)
class RequestUserAdmin(admin.ModelAdmin):
    """Список зарегистрированных поисковых запросов."""

    list_display = ("id", "search_phrase", "sity", "price_from", "price_to", "has_url")
    search_fields = ("search_phrase", "sity")

    @admin.display(boolean=True, description="URL")
    def has_url(self, obj):
        return bool(obj.url)


@admin.register(ResultParsing)
class ResultParsingAdmin(admin.ModelAdmin):
    """Результаты периодических замеров."""

    list_display = ("id", "request", "ads_count", "checked_at")
    list_filter = ("request",)
    date_hierarchy = "checked_at"
