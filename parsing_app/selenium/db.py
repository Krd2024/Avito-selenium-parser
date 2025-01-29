from parsing_app.models import RequestUser, ResultParsing
from loguru import logger


def create_result(data_parsing):
    # Сохраняем результаты в БД
    try:
        request_user = RequestUser.objects.get(id=data_parsing["request"])
        result = ResultParsing.objects.create(
            request=request_user,
            ads_count=data_parsing["ads_count"],
            checked_at=data_parsing["checked_at"],
        )
        print(
            f"Сохранен результат для ID: {result.request} (объявлений: {result.ads_count} время проверки: {result.checked_at})"
        )
    except Exception as e:
        logger.error(f"Ошибка - {e}")
