"""Прокси для обхода блокировок Авито: пул, ротация и учёт сбоев.

Авито очень быстро банит IP, с которого приходят автоматические запросы,
поэтому парсер поддерживает список прокси и их ротацию:

* каждый запуск браузера берёт следующий прокси из пула;
* если прокси «умер» или Авито показала капчу/403, прокси помечается
  сбойным и временно исключается из ротации (cooldown);
* при ошибке парсинга задача автоматически повторяется со следующим
  прокси (число попыток настраивается).

Список прокси берётся из двух источников (объединяются, дубли отбрасываются):

1. файл ``proxies.txt`` в корне проекта (путь меняется через ``PROXY_FILE``);
2. переменная окружения ``PROXY_LIST`` (через запятую).

Поддерживаемые форматы строк::

    host:port                      # без авторизации
    host:port:login:password       # с авторизацией
    login:password@host:port       # с авторизацией
    http://host:port               # со схемой
    socks5://login:password@host:port

Пустые строки и комментарии (начинаются с ``#``) игнорируются.

Переменные окружения:

========================  =================  ===========================================
Переменная                По умолчанию       Описание
========================  =================  ===========================================
``PROXY_FILE``            ``proxies.txt``    Файл со списком прокси (один на строку)
``PROXY_LIST``            пусто              Прокси через запятую прямо в окружении
``PROXY_ROTATION``        ``round_robin``    ``round_robin`` (по кругу) или ``random``
``PROXY_MAX_FAILURES``    ``3``              Сбоев до временного бана прокси
``PROXY_COOLDOWN_MINUTES`` ``30``            На сколько минут банить сбойный прокси
``PARSE_PROXY_ATTEMPTS``  ``3``              Сколько прокси перебрать на одну задачу
========================  =================  ===========================================

Если список прокси пуст, парсер работает напрямую (как раньше).
"""

from __future__ import annotations

import base64
import json
import os
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import unquote, urlparse

from loguru import logger

# Корень проекта: ../.. от parsing_app/selenium/proxy.py.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _env(name: str, default: str = "") -> str:
    """Читает переменную окружения.

    Используется прямой ``os.environ`` вместо ``python-decouple``, чтобы
    модуль оставался автономным (тесты, скрипты без Django). Значения из
    ``.env`` подхватывает docker-compose / сам decouple на уровне settings —
    при запуске через ``manage.py`` переменные уже есть в окружении.

    :param name: имя переменной.
    :param default: значение по умолчанию.
    :return: строковое значение.
    """
    value = os.environ.get(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Proxy:
    """Параметры одного прокси-сервера.

    :ivar host: адрес сервера (IP или домен).
    :ivar port: порт.
    :ivar username: логин (пустая строка, если авторизации нет).
    :ivar password: пароль (пустая строка, если авторизации нет).
    :ivar protocol: схема: ``http``, ``https``, ``socks5`` или ``socks4``.
    """

    host: str
    port: int
    username: str = ""
    password: str = ""
    protocol: str = "http"

    @property
    def key(self) -> str:
        """Уникальный идентификатор прокси (без пароля — для логов)."""
        auth = f"{self.username}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

    @property
    def has_auth(self) -> bool:
        """``True``, если прокси требует логин/пароль."""
        return bool(self.username)

    @property
    def chrome_server(self) -> str:
        """Значение для флага Chrome ``--proxy-server`` (без авторизации).

        Chrome принимает ``host:port`` для http(s) и ``socks5://host:port``
        для SOCKS. Логин/пароль сюда не попадает — Chrome не умеет
        передавать их через аргумент командной строки, для этого
        подключается мини-расширение (см. :func:`create_proxy_auth_extension`).
        """
        if self.protocol.startswith("socks"):
            return f"{self.protocol}://{self.host}:{self.port}"
        return f"{self.host}:{self.port}"

    def __str__(self) -> str:  # в логах пароль не показываем
        return self.key


def parse_proxy_line(raw: str) -> Optional[Proxy]:
    """Разбирает строку с прокси в объект :class:`Proxy`.

    Поддерживаются форматы::

        host:port
        host:port:login:password
        login:password@host:port
        http://host:port
        socks5://login:password@host:port

    :param raw: строка с описанием прокси.
    :return: :class:`Proxy` или ``None``, если строка пустая/комментарий/мусор.
    """
    line = (raw or "").strip()
    if not line or line.startswith("#"):
        return None

    protocol = "http"
    username = ""
    password = ""

    # Схема (http://, socks5:// ...) — вырезаем и запоминаем.
    if "://" in line:
        scheme, _, line = line.partition("://")
        protocol = scheme.strip().lower() or "http"

    # Авторизация через login:password@host:port. Разделитель «@» учитываем,
    # только если после него есть «host:port» — иначе «@» может быть частью
    # пароля в формате host:port:login:p@ss.
    if "@" in line:
        auth_part, _, host_part = line.rpartition("@")
        if ":" in host_part:
            if ":" in auth_part:
                username, _, password = auth_part.partition(":")
            else:
                username = auth_part
            username, password = unquote(username), unquote(password)
            line = host_part

    # host:port[:login:password] — формат «через двоеточие».
    parts = line.split(":")
    if len(parts) < 2:
        logger.warning(f"Пропущена некорректная строка прокси: {raw!r}")
        return None

    if len(parts) >= 4:
        # host:port:login:password (пароль может содержать «:»).
        host, port_raw = parts[0], parts[1]
        username = username or parts[2]
        password = password or ":".join(parts[3:])
    else:
        host, port_raw = parts[0], parts[1]

    host = host.strip()
    try:
        port = int(port_raw.strip())
    except ValueError:
        logger.warning(f"Пропущен прокси с некорректным портом: {raw!r}")
        return None

    if not host or not (0 < port < 65536):
        logger.warning(f"Пропущен прокси с некорректным адресом: {raw!r}")
        return None

    return Proxy(
        host=host,
        port=port,
        username=username.strip(),
        password=password.strip(),
        protocol=protocol if protocol.startswith("socks") or protocol in ("http", "https") else "http",
    )


def load_proxies_from_text(text: str) -> List[Proxy]:
    """Разбирает несколько строк (файл или переменную окружения).

    Разделители: перевод строки, запятая или точка с запятой.

    :param text: текст со списком прокси.
    :return: список валидных :class:`Proxy` (без дублей).
    """
    if not text:
        return []
    normalized = text.replace(";", "\n").replace(",", "\n")
    seen: Set[str] = set()
    result: List[Proxy] = []
    for chunk in normalized.splitlines():
        proxy = parse_proxy_line(chunk)
        if proxy is not None and proxy.key not in seen:
            seen.add(proxy.key)
            result.append(proxy)
    return result


def load_proxies_from_file(path: str | os.PathLike) -> List[Proxy]:
    """Читает список прокси из файла (одна строка на прокси).

    :param path: путь к файлу.
    :return: список :class:`Proxy`; если файла нет — пустой список.
    """
    path = Path(path)
    if not path.is_file():
        return []
    try:
        return load_proxies_from_text(path.read_text(encoding="utf-8"))
    except OSError as exc:
        logger.warning(f"Не удалось прочитать файл прокси {path}: {exc}")
        return []


def load_configured_proxies() -> List[Proxy]:
    """Собирает прокси из файла и переменной окружения.

    Порядок: сначала ``PROXY_FILE`` (по умолчанию ``proxies.txt`` в корне
    проекта), затем ``PROXY_LIST``. Дубли отбрасываются.

    :return: объединённый список :class:`Proxy`.
    """
    proxy_file = _env("PROXY_FILE") or str(BASE_DIR / "proxies.txt")
    proxies = load_proxies_from_file(proxy_file)
    proxies_env = load_proxies_from_text(_env("PROXY_LIST"))

    seen = {p.key for p in proxies}
    for proxy in proxies_env:
        if proxy.key not in seen:
            seen.add(proxy.key)
            proxies.append(proxy)

    if proxies:
        logger.info(f"Загружено прокси: {len(proxies)} (файл: {proxy_file})")
    else:
        logger.info("Прокси не заданы — парсер работает напрямую.")
    return proxies


@dataclass
class _ProxyState:
    """Внутреннее состояние прокси в пуле."""

    failures: int = 0
    banned_until: float = 0.0
    used_at: float = 0.0
    extra: Dict[str, object] = field(default_factory=dict)


class ProxyPool:
    """Потокобезопасный пул прокси с ротацией и временным баном сбойных.

    Планировщик запускает задачи парсинга в нескольких потоках
    (``ThreadPoolExecutor``), поэтому все операции защищены мьютексом.

    :param proxies: исходный список прокси.
    :param rotation: стратегия выбора: ``round_robin`` или ``random``.
    :param max_failures: сколько подряд сбоев терпеть до бана прокси.
    :param cooldown_seconds: длительность бана, сек.
    """

    def __init__(
        self,
        proxies: Iterable[Proxy],
        rotation: str = "round_robin",
        max_failures: int = 3,
        cooldown_seconds: float = 30 * 60,
    ) -> None:
        # dedup с сохранением порядка
        self._proxies: List[Proxy] = []
        seen: Set[str] = set()
        for proxy in proxies:
            if proxy.key not in seen:
                seen.add(proxy.key)
                self._proxies.append(proxy)

        self._states: Dict[str, _ProxyState] = {
            p.key: _ProxyState() for p in self._proxies
        }
        self._rotation = rotation if rotation in ("round_robin", "random") else "round_robin"
        self._max_failures = max(1, max_failures)
        self._cooldown_seconds = max(0.0, cooldown_seconds)
        self._index = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ API

    def __len__(self) -> int:
        return len(self._proxies)

    def __bool__(self) -> bool:
        return bool(self._proxies)

    @property
    def proxies(self) -> Tuple[Proxy, ...]:
        """Все прокси пула (кортеж — копия, чтобы не меняли извне)."""
        return tuple(self._proxies)

    def next(self, exclude: Optional[Iterable[str]] = None) -> Optional[Proxy]:
        """Выбирает следующий доступный прокси.

        Забаненные (на cooldown) прокси пропускаются. Если бан «протух»,
        счётчик сбоев прокси сбрасывается — даём ему второй шанс.

        :param exclude: ключи прокси, которые нужно пропустить (уже пробовали).
        :return: :class:`Proxy` или ``None``, если доступных нет.
        """
        excluded = set(exclude or ())
        now = time.monotonic()
        with self._lock:
            if not self._proxies:
                return None

            candidates = [
                p for p in self._proxies
                if p.key not in excluded and self._states[p.key].banned_until <= now
            ]
            # «Протухшие» баны сбрасываем, чтобы прокси снова участвовал.
            for proxy in self._proxies:
                state = self._states[proxy.key]
                if state.banned_until and state.banned_until <= now:
                    state.banned_until = 0.0
                    state.failures = 0
            if not candidates:
                return None

            if self._rotation == "random":
                proxy = random.choice(candidates)
            else:
                # Круговая ротация: идём по списку от текущего индекса.
                proxy = candidates[self._index % len(candidates)]
                self._index += 1

            self._states[proxy.key].used_at = now
            return proxy

    def report_success(self, proxy: Proxy) -> None:
        """Отмечает успешное использование: сбрасывает счётчик сбоев.

        :param proxy: прокси, через который запрос прошёл.
        """
        with self._lock:
            state = self._states.get(proxy.key)
            if state is not None:
                state.failures = 0
                state.banned_until = 0.0

    def report_failure(self, proxy: Proxy, reason: str = "", ban_now: bool = False) -> bool:
        """Отмечает сбой; после ``max_failures`` банит прокси на cooldown.

        :param proxy: сбойный прокси.
        :param reason: причина для лога.
        :param ban_now: забанить немедленно, не дожидаясь ``max_failures``
            (используется при капче — прокси уже точно спален).
        :return: ``True``, если прокси забанен после этого сбоя.
        """
        with self._lock:
            state = self._states.get(proxy.key)
            if state is None:
                return False
            state.failures += 1
            if ban_now:
                state.failures = max(state.failures, self._max_failures)
            if state.failures >= self._max_failures:
                state.banned_until = time.monotonic() + self._cooldown_seconds
                logger.warning(
                    f"Прокси {proxy} забанен на {self._cooldown_seconds / 60:.0f} мин "
                    f"после {state.failures} сбоев ({reason or 'без указания причины'}). "
                    "Возможно, прокси мертв или заблокирован Авито."
                )
                return True
            logger.debug(f"Сбой прокси {proxy} ({state.failures}/{self._max_failures}): {reason}")
            return False

    def stats(self) -> List[Dict[str, object]]:
        """Снимок состояния пула (для логов и отладки)."""
        now = time.monotonic()
        with self._lock:
            return [
                {
                    "proxy": p.key,
                    "failures": self._states[p.key].failures,
                    "banned": self._states[p.key].banned_until > now,
                }
                for p in self._proxies
            ]


# ------------------------------------------------------------------- пул-синглтон

_pool: Optional[ProxyPool] = None
_pool_lock = threading.Lock()


def get_proxy_pool(force_reload: bool = False) -> Optional[ProxyPool]:
    """Возвращает глобальный пул прокси (создаётся один раз).

    :param force_reload: перечитать конфигурацию (после смены ``proxies.txt``).
    :return: :class:`ProxyPool` или ``None``, если прокси не заданы.
    """
    global _pool
    with _pool_lock:
        if _pool is not None and not force_reload:
            return _pool

        proxies = load_configured_proxies()
        if not proxies:
            _pool = None
            return None

        try:
            max_failures = int(_env("PROXY_MAX_FAILURES", "3"))
        except ValueError:
            max_failures = 3
        try:
            cooldown_minutes = float(_env("PROXY_COOLDOWN_MINUTES", "30"))
        except ValueError:
            cooldown_minutes = 30.0

        _pool = ProxyPool(
            proxies,
            rotation=_env("PROXY_ROTATION", "round_robin"),
            max_failures=max_failures,
            cooldown_seconds=cooldown_minutes * 60,
        )
        return _pool


def max_attempts_for_pool(pool: Optional[ProxyPool]) -> int:
    """Сколько попыток (прокси) делать на одну задачу парсинга.

    Берётся ``PARSE_PROXY_ATTEMPTS`` (по умолчанию 3), но не больше размера
    пула. Если пул пуст — одна попытка напрямую.

    :param pool: пул прокси или ``None``.
    :return: число попыток (>= 1).
    """
    try:
        configured = int(_env("PARSE_PROXY_ATTEMPTS", "3"))
    except ValueError:
        configured = 3
    configured = max(1, configured)

    if pool is None or len(pool) == 0:
        return 1
    return min(configured, len(pool))


# ------------------------------------------------- применение прокси к Chrome

_MANIFEST_TEMPLATE = {
    "version": "1.0.0",
    "manifest_version": 3,
    "name": "Avito Parser Proxy Auth",
    "permissions": ["proxy", "declarativeNetRequest"],
    "host_permissions": ["<all_urls>"],
    "background": {"service_worker": "background.js"},
}

_BACKGROUND_TEMPLATE = """// Автогенерация: добавляет заголовок Proxy-Authorization для прокси с паролем.
const HEADER = {
  operation: "set",
  header: "Proxy-Authorization",
  value: "Basic __TOKEN__"
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: [1],
    addRules: [{
      id: 1,
      priority: 1,
      action: { type: "modifyHeaders", requestHeaders: [HEADER] },
      condition: {
        urlFilter: "|http",
        resourceTypes: [
          "main_frame", "sub_frame", "stylesheet", "script", "image",
          "font", "object", "xmlhttprequest", "ping", "csp_report",
          "media", "websocket", "other"
        ]
      }
    }]
  });
});
"""


def create_proxy_auth_extension(proxy: Proxy, directory: str | os.PathLike) -> Path:
    """Создаёт временное Chrome-расширение для прокси с авторизацией.

    Chrome не принимает ``login:password@host:port`` в аргументе
    ``--proxy-server``, поэтому для авторизованных прокси подключается
    мини-расширение (Manifest V3), которое подставляет заголовок
    ``Proxy-Authorization: Basic ...`` во все запросы.

    :param proxy: прокси с логином и паролем.
    :param directory: каталог, куда положить файлы расширения.
    :return: путь к каталогу расширения (его передают в ``--load-extension``).
    """
    ext_dir = Path(directory) / f"proxy_auth_{proxy.host}_{proxy.port}"
    ext_dir.mkdir(parents=True, exist_ok=True)

    token = base64.b64encode(
        f"{proxy.username}:{proxy.password}".encode("utf-8")
    ).decode("ascii")

    (ext_dir / "manifest.json").write_text(
        json.dumps(_MANIFEST_TEMPLATE, indent=2), encoding="utf-8"
    )
    (ext_dir / "background.js").write_text(
        _BACKGROUND_TEMPLATE.replace("__TOKEN__", token), encoding="utf-8"
    )
    return ext_dir


def apply_proxy_to_options(options, proxy: Optional[Proxy], temp_root: Optional[str | os.PathLike] = None) -> Optional[Path]:
    """Прописывает прокси в :class:`selenium.webdriver.ChromeOptions`.

    * без авторизации — достаточно флага ``--proxy-server``;
    * с авторизацией — дополнительно собирается временное расширение,
      а флаг ``--disable-extensions`` убирается (иначе расширение
      не загрузится).

    :param options: объект ``ChromeOptions``.
    :param proxy: прокси или ``None`` (ничего не делаем).
    :param temp_root: куда положить расширение с авторизацией
        (по умолчанию — системный temp).
    :return: путь к каталогу расширения (для очистки) или ``None``.
    """
    if proxy is None:
        return None

    options.add_argument(f"--proxy-server={proxy.chrome_server}")
    logger.info(f"Браузер поедет через прокси: {proxy}")

    if not proxy.has_auth:
        return None

    import tempfile

    root = Path(temp_root) if temp_root else Path(tempfile.gettempdir()) / "avito_parser_proxy_ext"
    ext_dir = create_proxy_auth_extension(proxy, root)
    options.add_argument(f"--load-extension={ext_dir}")
    logger.debug(f"Подключено расширение авторизации прокси: {ext_dir}")
    return ext_dir
