from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample

from parsing_app.drf.serializers import RequestUserSerializer, ResultParsingSerializer
from parsing_app.models import RequestUser, ResultParsing


class RequestSerializerSet(viewsets.ViewSet):
    """
    Метод /add Должен принимать поисковую фразу и регион,
    регистрировать их в системе. Возвращать id этой пары.

    Метод /stat Принимает на вход id связки поисковая фраза + регион
    и интервал, за который нужно вывести счётчики.
    Возвращает счётчики и соответствующие им временные метки (timestamp).

    Частота опроса = 1 раз в час  для каждого id
    """

    def get_quryset(self):
        return RequestUser.objects.all()

    def create(self, request):
        # Создаем экземпляр сериализатора с данными из запроса
        serializer = RequestUserSerializer(data=request.data)
        print(serializer)

        if serializer.is_valid():
            serializer.save()

    def list(self):

        queryset = self.get_quryset_result_parsing()
        serializer = ResultParsingSerializer(queryset, many=True)


class ResultParsingSet(viewsets.ViewSet):

    def get_quryset(self):
        return ResultParsing.objects.all()

    def list(self):
        pass

    # @extend_schema(
    #     description="Пример ViewSet для Avito",
    #     responses={200: None},  # Укажите ожидаемые ответы
    # )
    # def create(self, request):
    #     print("hello")
    #     return response.Response({"message": "Это пример ViewSet"})
