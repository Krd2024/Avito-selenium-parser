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
    # if headless:
    #     options.add_argument("--headless=new")
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


# Транслитерация кириллицы в латиницу для slug'ов Авито.
# Авито использует латиницу в URL: /moskva, /krasnodar, /sankt-peterburg, а не кириллицу.
# Прежняя реализация делала quote_plus(\"краснодар\") -> %D0%BA... и получала 404.
_CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",  # в URL Авито ё -> e (Орел, а не Oryol)
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def _transliterate_and_slugify_city(city: str) -> str:
    """Переводит название города в slug, который понимает Авито.

    - кириллица транслитерируется в латиницу (Москва -> moskva)
    - пробелы и подчеркивания становятся дефисами (Нижний Новгород -> nizhniy-novgorod)
    - оставляются только a-z, 0-9 и дефис
    - пустое значение -> 'all' (поиск по всей России)

    :param city: исходное название города (может быть на русском).
    :return: slug города в формате Авито.
    """
    raw = (city or "").strip().lower()
    if not raw:
        return "all"

    # Быстрый путь: если город уже латиницей и совпадает с all
    if raw == "all" or raw == "rossiya":
        return "all"

    # Транслитерация посимвольно, латиница и цифры остаются как есть
    transliterated_chars: list[str] = []
    for ch in raw:
        if ch in _CYRILLIC_TO_LATIN:
            transliterated_chars.append(_CYRILLIC_TO_LATIN[ch])
        else:
            transliterated_chars.append(ch)
    transliterated = "".join(transliterated_chars)

    # Нормализация: пробелы/_ -> -, убрать всё кроме a-z0-9-
    slug = transliterated.replace(" ", "-").replace("_", "-")
    # Заменяем любой символ, не входящий в a-z0-9-, на дефис
    slug = re.sub(r"[^a-z0-9-]", "-", slug)
    # Схлопываем множественные дефисы и обрезаем по краям
    slug = re.sub(r"-+", "-", slug).strip("-")

    return slug or "all"


def _encode_avito_price_filter(price_from: Optional[int], price_to: Optional[int]) -> str:
    """Кодирует ценовой диапазон в формат параметра ``f`` Avito.

    Avito хранит ценовые фильтры как base64-url-safe от JSON
    ``{"from":<N>,"to":<M>}`` внутри параметра ``f``.

    :param price_from: цена от (руб.) или ``None``.
    :param price_to: цена до (руб.) или ``None``.
    :return: строка вида ``&f=<base64>`` или пустая строка, если цен нет.
    """
    import base64
    import json

    if price_from is None and price_to is None:
        return ""

    payload = {}
    if price_from is not None:
        payload["from"] = price_from
    if price_to is not None:
        payload["to"] = price_to

    json_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(json_bytes).decode("ascii").rstrip("=")
    return f"&f={encoded}"


def build_search_url(
    product: str,
    city: str,
    *,
    url: str = "",
    price_from: Optional[int] = None,
    price_to: Optional[int] = None,
) -> str:
    """Формирует прямую ссылку на поиск вместо кликов по интерфейсу.

    Если задан ``url`` (полная ссылка от пользователя с фильтрами Avito),
    он используется как основа — к нему лишь добавляются ценовые фильтры,
    если они указаны.

    Если ``url`` не задан, URL строится автоматически из ``product`` и ``city``.

    Прежняя реализация выбирала город и вводила запрос через UI, опираясь на
    сгенерированные CSS-классы (``buyer-location-nev1ty`` и т.п.). Они меняются
    при каждом релизе Авито, поэтому парсер переставал работать. Прямой URL
    гораздо стабильнее.

    :param product: поисковая фраза.
    :param city: регион (город) поиска (может быть на русском).
    :param url: полный URL от пользователя с фильтрами (необязательно).
    :param price_from: цена от (руб., необязательно).
    :param price_to: цена до (руб., необязательно).
    :return: URL страницы результатов поиска.
    """
    from urllib.parse import quote_plus, urlparse, urlunparse

    price_filter = _encode_avito_price_filter(price_from, price_to)

    if url:
        # Пользовательский URL с фильтрами — используем как основу.
        # Добавляем ценовые фильтры, если они заданы.
        if price_filter:
            parsed = urlparse(url)
            sep = "&" if parsed.query else ""
            new_query = parsed.query + sep + price_filter.lstrip("&")
            url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment,
            ))
        return url

    city_slug = _transliterate_and_slugify_city(city)
    # product может содержать кириллицу — его кодируем через quote_plus
    product_q = quote_plus((product or "").strip())
    base = f"https://www.avito.ru/{city_slug}?q={product_q}"
    if price_filter:
        base += price_filter
    return base


async def selenium_task(data) -> None:
    """Асинхронная обертка для Selenium.

    :param data: кортеж ``(фраза, город, id связки)`` или
        ``(фраза, город, id связки, url, price_from, price_to)``.
    """
    await asyncio.to_thread(get_browser, data)


def get_browser(data) -> Optional[int]:
    """Парсит Авито и сохраняет количество найденных объявлений.

    :param data: кортеж ``(фраза, город, id связки)`` или
        ``(фраза, город, id связки, url, price_from, price_to)``.
    :return: количество объявлений или ``None``, если получить его не удалось.
    """
    # Поддержка расширенного формата с фильтрами.
    if len(data) >= 6:
        product, city, task_id, url, price_from, price_to = data[:6]
    else:
        product, city, task_id = data[:3]
        url = ""
        price_from = None
        price_to = None

    logger.info(
        f"Старт парсинга: фраза={product!r}, город={city!r}, id={task_id}, "
        f"url={url!r}, цена={price_from}–{price_to}"
    )

    browser = None
    try:
        browser = webdriver.Chrome(options=build_options())
        browser.set_page_load_timeout(60)
        browser.get(build_search_url(
            product, city,
            url=url,
            price_from=price_from,
            price_to=price_to,
        ))

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
