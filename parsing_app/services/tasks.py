from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def hourly_task(*args):
    print("Hourly Task")
    phrase, city = args[0]  # Распаковываем данные
    logger.info(f"Задача выполняется в {datetime.now()}")
    logger.info(f"Поиск по фразе: '{phrase}' в городе: '{city}'")
