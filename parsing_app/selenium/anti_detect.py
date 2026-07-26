"""Анти-детект меры: ротация User-Agent и эмуляция поведения пользователя."""

import random
import time
from typing import Optional

from selenium.webdriver import Chrome
from selenium.webdriver.common.action_chains import ActionChains
from loguru import logger


# Пул реальных User-Agent'ов для ротации
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def get_random_user_agent() -> str:
    """Возвращает случайный User-Agent из пула.
    
    :return: строка User-Agent
    """
    return random.choice(USER_AGENTS)


def human_like_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    """Случайная задержка для эмуляции поведения человека.
    
    :param min_seconds: минимальная задержка
    :param max_seconds: максимальная задержка
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def random_scroll(browser: Chrome) -> None:
    """Случайный скролл страницы для эмуляции пользователя.
    
    :param browser: экземпляр Chrome WebDriver
    """
    try:
        # Случайная высота скролла (100-500px)
        scroll_amount = random.randint(100, 500)
        scroll_direction = random.choice(["down", "up", "down"])  # чаще вниз
        
        if scroll_direction == "down":
            browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
        else:
            browser.execute_script(f"window.scrollBy(0, -{scroll_amount});")
        
        human_like_delay(0.3, 1.0)
        logger.debug(f"Скролл страницы: {scroll_direction} на {scroll_amount}px")
    except Exception as e:
        logger.warning(f"Не удалось выполнить скролл: {e}")


def random_mouse_movement(browser: Chrome, element=None) -> None:
    """Случайное движение мыши для эмуляции пользователя.
    
    :param browser: экземпляр Chrome WebDriver
    :param element: целевой элемент (опционально)
    """
    try:
        actions = ActionChains(browser)
        
        # Случайные движения в пределах страницы
        for _ in range(random.randint(1, 3)):
            x_offset = random.randint(-50, 50)
            y_offset = random.randint(-50, 50)
            actions.move_by_offset(x_offset, y_offset)
            human_like_delay(0.1, 0.3)
        
        # Если есть целевой элемент, двигаемся к нему
        if element is not None:
            actions.move_to_element(element)
            human_like_delay(0.2, 0.5)
        
        actions.perform()
        logger.debug("Случайное движение мыши выполнено")
    except Exception as e:
        logger.warning(f"Не удалось выполнить движение мыши: {e}")


def simulate_human_behavior(browser: Chrome, pre_action: bool = False) -> None:
    """Эмуляция поведения человека перед действием.
    
    :param browser: экземпляр Chrome WebDriver
    :param pre_action: если True, более длительная эмуляция перед важным действием
    """
    try:
        # Случайный скролл
        random_scroll(browser)
        
        # Случайные движения мыши
        random_mouse_movement(browser)
        
        # Если это перед важным действием, добавляем дополнительную задержку
        if pre_action:
            human_like_delay(1.0, 3.0)
            # Ещё один скролл
            random_scroll(browser)
        
        logger.debug("Эмуляция поведения человека завершена")
    except Exception as e:
        logger.warning(f"Ошибка при эмуляции поведения: {e}")


def wait_after_critical_action(browser: Chrome, min_wait: float = 5.0, max_wait: float = 10.0) -> None:
    """Длительное ожидание после критического действия (например, переключение фильтра).
    
    :param browser: экземпляр Chrome WebDriver
    :param min_wait: минимальное время ожидания
    :param max_wait: максимальное время ожидания
    """
    try:
        wait_time = random.uniform(min_wait, max_wait)
        logger.info(f"Ожидание {wait_time:.1f} сек после критического действия...")
        
        # Во время ожидания эмулируем поведение пользователя
        for _ in range(random.randint(2, 4)):
            random_scroll(browser)
            human_like_delay(0.5, 1.5)
        
        time.sleep(wait_time)
        logger.info("Ожидание завершено")
    except Exception as e:
        logger.warning(f"Ошибка при ожидании: {e}")
