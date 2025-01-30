from rest_framework import serializers

from parsing_app.models import RequestUser, ResultParsing

# from parsing_app import RequestUser, ResultParsing


class RequestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestUser
        fields = "__all__"

    def create(self, validated_data):
        """
        Проверить есть ли уже такие запросы
        """
        # Извлекаем данные из validated_data
        search_phrase_value = validated_data.get("search_phrase")
        sity_value = validated_data.get("sity")
        # other_field_value = validated_data.get("other_field")
        # RequestUser.objects.filter(
        #     search_phrase=search_phrase_value, sity=sity_value
        # ).delete()

        result, created = RequestUser.objects.get_or_create(
            search_phrase=search_phrase_value.lower(),
            sity=sity_value.lower(),
            # defaults={"other_field": other_field_value},
        )

        # Возвращаем найденный или созданный объект
        return result


class ResultParsingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultParsing
        fields = ["ads_count", "checked_at", "request"]
