from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime
from loguru import logger
import asyncio
import time

from parsing_app.selenium.db import create_result


options = webdriver.ChromeOptions()

options.add_argument("--disable-gpu")
options.add_argument("--ignore-certificate-errors")
# options.add_argument("--disable-javascript")  # Отключение JavaScript
# options.add_argument("--blink-settings=imagesEnabled=false")  # Отключение изображений
# options.add_argument("--headless")  # Фоновый режим
# options.add_argument(
#     "--disable-blink-features=AutomationControlled"
# )  # Скрываем автоматизацию

city = "краснодар"


async def selenium_task(data):
    """Асинхронная обертка для Selenium"""
    await asyncio.to_thread(get_browser, data)


def get_browser(data):
    """Парсинг сайта"""

    product, city, task_id = data
    logger.info(data)
    data_parsing = {}

    with webdriver.Chrome(options=options) as browser:
        browser.get("https://avito.ru")

        # ------------------------------ Выбор города -------------------------------------
        # выбор города
        time.sleep(5)
        # browser.find_element(
        #     By.CSS_SELECTOR, "div.main-richTitleWrapper__content-mSHt1"
        # ).click()  # Выбор города

        browser.find_element(
            By.CSS_SELECTOR, "span.buyer-location-nev1ty"
        ).click()  # Выбор города
        time.sleep(3)

        # поле ввода города
        input_city = browser.find_element(
            By.CSS_SELECTOR, "input.styles-module-searchInput-fm9ey"
        )

        time.sleep(0.1)
        input_city.click()  # перейти к полю
        time.sleep(0.1)
        input_city.clear()  # очистить
        time.sleep(0.1)
        for i in city:
            input_city.send_keys(i)
            time.sleep(0.3)
        time.sleep(2)

        button = browser.find_element(
            By.CSS_SELECTOR,
            "button.styles-module-root-hUB0x.styles-module-root_size_s-OErXY.styles-module-root_preset_primary-BrO4Z",
        )
        # button = browser.find_element(
        #     By.CSS_SELECTOR, "button[data-marker='popup-location/save-button']"
        # )
        browser.execute_script("arguments[0].click();", button)
        time.sleep(2)
        # ---------------------------------------------------------------------------------

        input_elem = browser.find_element(
            By.CSS_SELECTOR, "input.styles-module-input-rA1dB"
        )  # поле поиска

        input_elem.send_keys(product)  # объект поиска

        button = browser.find_element(
            By.CLASS_NAME, "buyer-location-xp6ezn"
        ).click()  # start поиск

        time.sleep(2)
        try:

            total = browser.find_element(
                By.CSS_SELECTOR, "span[data-marker='page-title/count']"
            ).text  # получить кол-во

            total = int(
                total.replace(" объявлений", "").replace(" ", "")
            )  # убрать пробелы и заменить на число

            logger.info(
                f"\n{'-'*80}\nВсего объявлений: {total} время проверки {datetime.now()} (Перед сохранением в бд)\n{'-'*80}"
            )

            data_parsing["ads_count"] = total
            data_parsing["checked_at"] = datetime.now()
            data_parsing["request"] = int(task_id)

            logger.info(f"Результат: {data_parsing}")

            # записать данные в базу данных
            create_result(data_parsing)

        except Exception as e:
            logger.error(f"Ошибка {e}")
