from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample


class AvitoSerializerSet(viewsets.ViewSet):
    """
    Метод /add Должен принимать поисковую фразу и регион,
    регистрировать их в системе. Возвращать id этой пары.

    Метод /stat Принимает на вход id связки поисковая фраза + регион
    и интервал, за который нужно вывести счётчики.
    Возвращает счётчики и соответствующие им временные метки (timestamp).

    Частота опроса = 1 раз в час  для каждого id
    """

    @extend_schema(
        description="Пример ViewSet для Avito",
        responses={200: None},  # Укажите ожидаемые ответы
    )
    def list(self, request):
        return response.Response({"message": "Это пример ViewSet"})
