"""Тесты для анти-детект модуля."""

import unittest
from parsing_app.selenium.anti_detect import (
    get_random_user_agent,
    human_like_delay,
    USER_AGENTS,
)


class TestAntiDetect(unittest.TestCase):
    """Тесты анти-детект функциональности."""
    
    def test_user_agents_pool_not_empty(self):
        """Проверяем, что пул User-Agent'ов не пуст."""
        self.assertGreater(len(USER_AGENTS), 0)
    
    def test_get_random_user_agent(self):
        """Проверяем, что get_random_user_agent возвращает строку из пула."""
        ua = get_random_user_agent()
        self.assertIsInstance(ua, str)
        self.assertIn(ua, USER_AGENTS)
    
    def test_user_agents_variety(self):
        """Проверяем, что User-Agent'ы разнообразны."""
        user_agents_set = set(USER_AGENTS)
        self.assertGreater(len(user_agents_set), 5)
    
    def test_human_like_delay(self):
        """Проверяем, что human_like_delay работает без ошибок."""
        import time
        start = time.time()
        human_like_delay(0.1, 0.2)
        elapsed = time.time() - start
        self.assertGreater(elapsed, 0.05)
        self.assertLess(elapsed, 0.5)


if __name__ == "__main__":
    unittest.main()
