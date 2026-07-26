"""Скрапинг Авито: получение количества объявлений по фразе и региону."""

from datetime import datetime
from typing import Optional, Tuple
import asyncio
import re

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from parsing_app.selenium.db import create_result

# Таймаут ожидания элементов на странице, сек.
WAIT_TIMEOUT = 20

# Селекторы вынесены в константы: вёрстка Авито регулярно меняется,
# и для каждого элемента перебирается несколько вариантов.
COUNT_SELECTORS = (
    "span[data-marker='page-title/count']",
    "h1[data-marker='page-title/text']",
    "[data-marker='page-title/count']",
)
SEARCH_INPUT_SELECTORS = (
    "input[data-marker='search-form/suggest/input']",
    "input[data-marker='search-form/suggest']",
    "input#search",
    "input.styles-module-input-rA1dB",
)


def build_options(headless: bool = True) -> webdriver.ChromeOptions:
    """Собирает параметры запуска Chrome.

    :param headless: запускать браузер в фоновом режиме.
    :return: сконфигурированный объект :class:`ChromeOptions`.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    # Обязательно в контейнере: без этих флагов Chrome падает в Docker.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    return options


def parse_ads_count(raw_text: str) -> Optional[int]:
    """Извлекает число объявлений из текста заголовка.

    Старый вариант делал ``int(text.replace(" объявлений", "").replace(" ", ""))``
    и падал на «121 261 объявление» (другое окончание) и на неразрывных
    пробелах (``\\xa0``, ``\\u202f``), которыми Авито разделяет разряды.

    :param raw_text: текст вида «121 261 объявление».
    :return: количество объявлений или ``None``, если чисел в строке нет.
    """
    digits = re.sub(r"\D", "", raw_text or "")
    return int(digits) if digits else None


def _find_first(browser, selectors: Tuple[str, ...], timeout: int = WAIT_TIMEOUT):
    """Возвращает первый найденный по списку селекторов элемент.

    :param browser: экземпляр WebDriver.
    :param selectors: CSS-селекторы в порядке приоритета.
    :param timeout: сколько ждать появления элемента, сек.
    :return: найденный элемент или ``None``.
    """
    for selector in selectors:
        try:
            return WebDriverWait(browser, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            continue
    return None


def build_search_url(product: str, city: str) -> str:
    """Формирует прямую ссылку на поиск вместо кликов по интерфейсу.

    Прежняя реализация выбирала город и вводила запрос через UI, опираясь на
    сгенерированные CSS-классы (``buyer-location-nev1ty`` и т.п.). Они меняются
    при каждом релизе Авито, поэтому парсер переставал работать. Прямой URL
    гораздо стабильнее.

    :param product: поисковая фраза.
    :param city: регион (город) поиска.
    :return: URL страницы результатов поиска.
    """
    from urllib.parse import quote_plus

    city_slug = (city or "").strip().lower().replace(" ", "_")
    city_slug = city_slug or "all"
    return f"https://www.avito.ru/{quote_plus(city_slug)}?q={quote_plus(product)}"


async def selenium_task(data: Tuple[str, str, int]) -> None:
    """Асинхронная обертка для Selenium.

    :param data: кортеж «(фраза, город, id связки)».
    """
    await asyncio.to_thread(get_browser, data)


def get_browser(data: Tuple[str, str, int]) -> Optional[int]:
    """Парсит Авито и сохраняет количество найденных объявлений.

    :param data: кортеж «(фраза, город, id связки)».
    :return: количество объявлений или ``None``, если получить его не удалось.
    """
    product, city, task_id = data
    logger.info(f"Старт парсинга: фраза={product!r}, город={city!r}, id={task_id}")

    browser = None
    try:
        browser = webdriver.Chrome(options=build_options())
        browser.set_page_load_timeout(60)
        browser.get(build_search_url(product, city))

        element = _find_first(browser, COUNT_SELECTORS)
        if element is None:
            # Запасной путь: город//фраза могли не примениться из URL —
            # пробуем ввести запрос в поле поиска.
            search_input = _find_first(browser, SEARCH_INPUT_SELECTORS, timeout=10)
            if search_input is not None:
                search_input.clear()
                search_input.send_keys(product)
                search_input.send_keys(Keys.ENTER)
                element = _find_first(browser, COUNT_SELECTORS)

        if element is None:
            logger.error(
                f"Не удалось найти счётчик объявлений для {product!r} ({city!r}). "
                "Возможно, изменилась вёрстка Авито или сработала антибот-защита."
            )
            return None

        total = parse_ads_count(element.text)
        if total is None:
            logger.error(f"Не удалось разобрать количество объявлений: {element.text!r}")
            return None

        logger.info(
            f"\n{'-' * 80}\nВсего объявлений: {total} "
            f"время проверки {datetime.now()} (перед сохранением в БД)\n{'-' * 80}"
        )

        data_parsing = {
            "ads_count": total,
            "checked_at": datetime.now(),
            "request": int(task_id),
        }
        logger.info(f"Результат: {data_parsing}")

        # Записать данные в базу данных
        create_result(data_parsing)
        return total

    except WebDriverException as exc:
        logger.error(f"Ошибка браузера при парсинге {product!r} ({city!r}): {exc}")
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Ошибка {exc}")
        return None
    finally:
        # Раньше браузер закрывался только при удачном сценарии `with`,
        # а падение до его создания оставляло висящие процессы chromedriver.
        if browser is not None:
            try:
                browser.quit()
            except Exception:  # noqa: BLE001
                pass
