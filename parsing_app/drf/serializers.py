from parsing_app.models import RequestUser, ResultParsing
from rest_framework import serializers

# from datetime import datetime


class RequestUserSerializer(serializers.ModelSerializer):
    """Сериализатор пары «поисковая фраза + регион» для метода /add."""

    search_phrase = serializers.CharField(
        max_length=255, allow_blank=False, trim_whitespace=True
    )
    sity = serializers.CharField(
        max_length=255, allow_blank=False, trim_whitespace=True
    )

    class Meta:
        model = RequestUser
        fields = ["id", "search_phrase", "sity"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict) -> RequestUser:
        """Возвращает существующую связку или создаёт новую.

        Оба поля обязательны и приводятся к нижнему регистру, поэтому
        «Москва» и «москва» считаются одним и тем же регионом.

        :param validated_data: провалидированные данные запроса.
        :return: найденный или созданный объект :class:`RequestUser`.
        """
        # Поля объявлены как required, поэтому здесь они всегда присутствуют:
        # раньше отсутствующий "sity" приводил к AttributeError и ответу 500.
        search_phrase_value = validated_data["search_phrase"].strip().lower()
        sity_value = validated_data["sity"].strip().lower()

        result, _created = RequestUser.objects.get_or_create(
            search_phrase=search_phrase_value,
            sity=sity_value,
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
