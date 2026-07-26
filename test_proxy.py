"""Тесты модуля прокси: парсинг строк, ротация, бан сбойных прокси."""

import unittest

from parsing_app.selenium.proxy import (
    Proxy,
    ProxyPool,
    load_proxies_from_text,
    max_attempts_for_pool,
    parse_proxy_line,
)


class TestParseProxy(unittest.TestCase):
    """Разбор строк с прокси."""

    def test_host_port(self):
        proxy = parse_proxy_line("185.204.0.1:8000")
        self.assertIsNotNone(proxy)
        self.assertEqual(proxy.host, "185.204.0.1")
        self.assertEqual(proxy.port, 8000)
        self.assertEqual(proxy.protocol, "http")
        self.assertFalse(proxy.has_auth)

    def test_host_port_login_password(self):
        proxy = parse_proxy_line("10.0.0.1:3128:user1:p@ss")
        self.assertIsNotNone(proxy)
        self.assertEqual((proxy.host, proxy.port), ("10.0.0.1", 3128))
        self.assertEqual(proxy.username, "user1")
        self.assertEqual(proxy.password, "p@ss")
        self.assertTrue(proxy.has_auth)

    def test_login_at_host(self):
        proxy = parse_proxy_line("login:password@10.0.0.2:1080")
        self.assertIsNotNone(proxy)
        self.assertEqual((proxy.host, proxy.port), ("10.0.0.2", 1080))
        self.assertEqual((proxy.username, proxy.password), ("login", "password"))

    def test_scheme_socks5(self):
        proxy = parse_proxy_line("socks5://u:p@10.0.0.3:1080")
        self.assertIsNotNone(proxy)
        self.assertEqual(proxy.protocol, "socks5")
        self.assertEqual(proxy.chrome_server, "socks5://10.0.0.3:1080")

    def test_http_scheme_stripped_in_chrome_server(self):
        proxy = parse_proxy_line("http://10.0.0.4:8080")
        self.assertEqual(proxy.chrome_server, "10.0.0.4:8080")

    def test_garbage_lines_skipped(self):
        self.assertIsNone(parse_proxy_line(""))
        self.assertIsNone(parse_proxy_line("# comment"))
        self.assertIsNone(parse_proxy_line("just-a-host"))
        self.assertIsNone(parse_proxy_line("host:not-a-port"))

    def test_load_text_dedup_and_comments(self):
        text = """
        # мой список
        10.0.0.1:8000
        10.0.0.1:8000
        10.0.0.2:8000, socks5://10.0.0.3:1080
        """
        proxies = load_proxies_from_text(text)
        self.assertEqual(len(proxies), 3)


class TestProxyPool(unittest.TestCase):
    """Ротация и бан прокси."""

    def setUp(self):
        self.proxies = [
            Proxy("10.0.0.1", 8000),
            Proxy("10.0.0.2", 8000),
            Proxy("10.0.0.3", 8000),
        ]

    def test_round_robin_rotation(self):
        pool = ProxyPool(self.proxies, rotation="round_robin")
        keys = [pool.next().key for _ in range(6)]
        # Идём по кругу: первые три различны, затем повторяются.
        self.assertEqual(len(set(keys[:3])), 3)
        self.assertEqual(keys[0], keys[3])

    def test_exclude(self):
        pool = ProxyPool(self.proxies)
        picked = pool.next(exclude={p.key for p in self.proxies[:2]})
        self.assertEqual(picked.host, "10.0.0.3")

    def test_ban_after_max_failures(self):
        pool = ProxyPool(self.proxies, max_failures=2, cooldown_seconds=60)
        bad = self.proxies[0]
        self.assertFalse(pool.report_failure(bad, reason="timeout"))
        self.assertTrue(pool.report_failure(bad, reason="timeout"))
        # Забаненный прокси больше не выдаётся.
        for _ in range(10):
            picked = pool.next()
            self.assertIsNotNone(picked)
            self.assertNotEqual(picked.key, bad.key)

    def test_ban_now(self):
        pool = ProxyPool(self.proxies, max_failures=3)
        bad = self.proxies[1]
        self.assertTrue(pool.report_failure(bad, reason="captcha", ban_now=True))

    def test_success_resets_failures(self):
        pool = ProxyPool(self.proxies, max_failures=2)
        proxy = self.proxies[0]
        pool.report_failure(proxy, reason="x")
        pool.report_success(proxy)
        # После успеха снова нужно два сбоя до бана.
        self.assertFalse(pool.report_failure(proxy, reason="x"))

    def test_all_banned_returns_none(self):
        pool = ProxyPool(self.proxies, max_failures=1, cooldown_seconds=60)
        for proxy in self.proxies:
            pool.report_failure(proxy, reason="x")
        self.assertIsNone(pool.next())

    def test_empty_pool(self):
        pool = ProxyPool([])
        self.assertIsNone(pool.next())
        self.assertFalse(pool)

    def test_max_attempts_for_pool(self):
        pool = ProxyPool(self.proxies)
        self.assertEqual(max_attempts_for_pool(pool), 3)
        self.assertEqual(max_attempts_for_pool(None), 1)
        small = ProxyPool([Proxy("10.0.0.1", 1)])
        self.assertEqual(max_attempts_for_pool(small), 1)


class TestProxyAuthExtension(unittest.TestCase):
    """Генерация расширения для прокси с паролем."""

    def test_extension_files_created(self):
        import tempfile

        from parsing_app.selenium.proxy import create_proxy_auth_extension

        proxy = Proxy("10.0.0.5", 3128, username="user", password="pass")
        with tempfile.TemporaryDirectory() as tmp:
            ext_dir = create_proxy_auth_extension(proxy, tmp)
            self.assertTrue((ext_dir / "manifest.json").is_file())
            background = (ext_dir / "background.js").read_text(encoding="utf-8")
            self.assertIn("Proxy-Authorization", background)
            self.assertIn("dXNlcjpwYXNz", background)  # base64("user:pass")


if __name__ == "__main__":
    unittest.main()
