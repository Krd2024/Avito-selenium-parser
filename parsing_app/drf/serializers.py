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
            # defaults={"other_field": other_field_value},
        )

        # Возвращаем найденный или созданный объект
        return result


class ResultParsingSerializer(serializers.Serializer):
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
    class Meta:
        model = ResultParsing
        fields = ["ads_count", "checked_at", "request"]
