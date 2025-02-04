from drf_spectacular.utils import extend_schema, OpenApiExample
from loguru import logger
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response


from parsing_app.drf.serializers import (
    AnswerParsingSerializer,
    RequestUserSerializer,
    ResultParsingSerializer,
)
from parsing_app.models import RequestUser, ResultParsing
from parsing_app.services.service import start_search

# from rest_framework.permissions import IsAuthenticated
# from django.utils import timezone


class RequestSerializerSet(viewsets.ViewSet):
    serializer_class = RequestUserSerializer
    """
    Метод /add Должен принимать поисковую фразу и регион,
    регистрировать их в системе. Возвращать id этой пары.

    Метод /stat Принимает на вход id связки поисковая фраза + регион
    и интервал, за который нужно вывести счётчики.
    Возвращает счётчики и соответствующие им временные метки (timestamp).

    Частота опроса = 1 раз в час  для каждого id
    """

    def get_queryset(self):
        return RequestUser.objects.all()

    @extend_schema(
        summary="Создаёт новую задачу для поиска",
        description="Создание новой задачи.\
                    Текущий пользователь указывается автоматически",
        request=RequestUserSerializer,
        responses={
            201: RequestUserSerializer,
            400: {"description": "Некорректные данные"},
        },
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={"search_phrase": "ноутбук", "sity": "Москва"},
                description="Пример создания новой задачи для поиска",
            ),
        ],
    )
    def create(self, request):

        # Создаем экземпляр сериализатора с данными из запроса
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            instance = serializer.save()

            # print(instance.id)
            # Передаёт объект поиска (что искать,город ,ID поиска) в сервис
            # сервис запускает планировщик с поиском по параметрам
            start_search(object_search=instance)

            return Response({"id": instance.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResultParsingSet(viewsets.ViewSet):
    serializer_class = ResultParsingSerializer

    @extend_schema(
        summary="Получить результаты статистики за период",
        description="Возвращает результаты статистики за указанный период времени.",
        request=ResultParsingSerializer,
        responses={
            200: ResultParsingSerializer(many=True),
            400: {"description": "Некорректные данные"},
        },
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={
                    "request_id": 1,
                    "start_search": "2025-01-01 12:00",
                    "end_search": "2026-01-01 12:00",
                },
                description="Пример получения результатов за период",
            ),
        ],
    )
    # def list(self, request, request_id, start, end):
    def create(self, request):
        results_test = ResultParsing.objects.all()
        for result in results_test:
            logger.info(
                f"Кол-во: {result.ads_count} Время проверки: {result.checked_at} ID: {result.request_id}"
            )

        serializer = self.serializer_class(data=request.data)
        # logger.debug(serializer)

        if serializer.is_valid():

            print(serializer.validated_data)

        # search(request_id, start, end)

        # Получить данные из запроса
        start = serializer.validated_data["start_search"]
        end = serializer.validated_data["end_search"]
        request_id = serializer.validated_data["request_id"]

        # Фильтруем результаты по request_id и периоду
        results = ResultParsing.objects.filter(
            request_id=request_id,
            checked_at__gte=start,
            checked_at__lte=end,
        ).order_by("checked_at")

        for result in results:
            print(
                f"Поиск: {result.request}\nКоличество: {result.ads_count}\nВремя проверки: {result.checked_at}\n"
            )

        serializer = AnswerParsingSerializer(results, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
