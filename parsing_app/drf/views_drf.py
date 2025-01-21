from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample

from parsing_app.drf.serializers import RequestUserSerializer, ResultParsingSerializer
from parsing_app.models import RequestUser, ResultParsing
from parsing_app.services.service import search


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
        # serializer = RequestUserSerializer(data=request.data)

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            instance = serializer.save()
            return Response({"id": instance.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResultParsingSet(viewsets.ViewSet):
    serializer_class = ResultParsingSerializer

    @extend_schema(
        summary="Получить результаты статистики за период",
        description="Возвращает результаты статистики за указанный период времени.",
        parameters=[
            OpenApiParameter(
                name="request_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID задачи",
            ),
            OpenApiParameter(
                name="start",
                type=str,
                location=OpenApiParameter.PATH,
                description="Начальная дата и время в формате 'YYYY-MM-DD HH:MM'",
            ),
            OpenApiParameter(
                name="end",
                type=str,
                location=OpenApiParameter.PATH,
                description="Конечная дата и время в формате 'YYYY-MM-DD HH:MM'",
            ),
        ],
        responses={
            200: ResultParsingSerializer(many=True),
            400: {"description": "Некорректные данные"},
        },
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={
                    "request": 1,
                    "start": "2025-01-01 12:00",
                    "end": "2025-01-01 12:00",
                },
                description="Пример получения результатов за период",
            ),
        ],
    )
    def list(self, request, request_id, start, end):

        search(request_id, start, end)

        try:
            # Преобразуем start и end в datetime
            from datetime import datetime

            start_date = datetime.strptime(start, "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(end, "%Y-%m-%d %H:%M")
        except ValueError:
            return Response(
                {"error": "Некорректный формат даты. Используйте 'YYYY-MM-DD HH:MM'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Фильтруем результаты по request_id и периоду
        results = ResultParsing.objects.filter(
            request_id=request_id,
            checked_at__gte=start_date,
            checked_at__lte=end_date,
        ).order_by("checked_at")

        # Сериализуем результаты
        serializer = self.serializer_class(results, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    # @extend_schema(
    #     description="Пример ViewSet для Avito",
    #     responses={200: None},  # Укажите ожидаемые ответы
    # )
    # def create(self, request):
    #     print("hello")
    #     return response.Response({"message": "Это пример ViewSet"})
