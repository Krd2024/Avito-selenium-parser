from parsing_app.models import RequestUser, ResultParsing
from rest_framework import serializers

# from datetime import datetime


class RequestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestUser
        fields = "__all__"

    def create(self, validated_data):
        """Проверить есть ли уже такие запросы"""

        # Извлекаем данные из validated_data
        search_phrase_value = validated_data.get("search_phrase")
        sity_value = validated_data.get("sity")

        result, created = RequestUser.objects.get_or_create(
            search_phrase=search_phrase_value.lower(),
            sity=sity_value.lower(),
        )

        # Возвращаем найденный или созданный объект
        return result


class ResultParsingSerializer(serializers.Serializer):
    """
    Сериализатор для валидации данных о процессе парсинга.

    Атрибуты:
    - start_search (datetime): Дата и время начала поиска.
    - end_search (datetime): Дата и время окончания поиска.
    - request_id (int): Идентификатор поискового запроса.
    """

    start_search = serializers.DateTimeField(format="%Y-%m-%d %H:%M", required=True)
    end_search = serializers.DateTimeField(format="%Y-%m-%d %H:%M", required=True)
    request_id = serializers.IntegerField(required=True)

    def validate(self, data):
        """
        Проверяет, что end_search позже start_search.
        """
        start = data.get("start_search")
        end = data.get("end_search")

        if end <= start:
            raise serializers.ValidationError(
                "Дата окончания должна быть позже даты начала."
            )

        return data


class AnswerParsingSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ответа с результатами парсинга.

    - ads_count (int): Количество найденных объявлений.
    - checked_at (datetime): Время проверки.
    - request (int): Связанный поисковый запрос.
    """

    class Meta:
        model = ResultParsing
        fields = ["ads_count", "checked_at", "request"]
