"""Точка входа для десктопного запуска (в том числе из собранного .exe).

Скрипт делает всё, что при обычной установке приходится делать руками:

1. применяет миграции (создаёт ``db.sqlite3`` рядом с .exe при первом старте);
2. поднимает локальный веб-сервер (waitress — чистый Python, работает
   на Windows без зависимостей);
3. открывает интерфейс в браузере по умолчанию.

Запуск в обычном окружении::

    python run_app.py            # http://127.0.0.1:8000
    python run_app.py --port 8100 --no-browser

Внутри .exe используется тот же файл — см. ``windows/avito_parser.spec``.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import webbrowser

# Настройки Django должны быть известны до любого импорта из проекта.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parsing_project.settings")

# Значение по умолчанию для десктопного запуска: пользователю нужен рабочий
# сервис «из коробки», без создания .env. Реальный .env, если он лежит рядом
# с .exe, всё равно имеет приоритет — его читает settings.py.
os.environ.setdefault("DB_ENGINE", "sqlite")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Разбирает аргументы командной строки.

    :param argv: аргументы без имени программы.
    :return: пространство имён с параметрами запуска.
    """
    parser = argparse.ArgumentParser(
        prog="AvitoParser",
        description="Локальный запуск сервиса отслеживания объявлений Авито.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Адрес сервера.")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Порт сервера."
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Не открывать браузер автоматически.",
    )
    return parser.parse_args(argv)


def _port_is_free(host: str, port: int) -> bool:
    """Проверяет, свободен ли TCP-порт.

    :param host: адрес для проверки.
    :param port: номер порта.
    :return: ``True``, если порт можно занять.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def pick_port(host: str, preferred: int, attempts: int = 20) -> int:
    """Возвращает свободный порт, начиная с предпочтительного.

    Если 8000 занят (частая ситуация на рабочей машине), приложение не падает,
    а поднимается на следующем свободном порту.

    :param host: адрес, на котором слушает сервер.
    :param preferred: желаемый порт.
    :param attempts: сколько портов подряд перебрать.
    :return: свободный порт.
    :raises RuntimeError: если свободный порт не найден.
    """
    for port in range(preferred, preferred + attempts):
        if _port_is_free(host, port):
            return port
    raise RuntimeError(
        f"Не удалось найти свободный порт в диапазоне "
        f"{preferred}-{preferred + attempts - 1}."
    )


def run_migrations() -> None:
    """Применяет миграции без обращения к файловой системе за командами.

    ``call_command("migrate")`` ищет команды перебором файлов в каталоге
    ``django/core/management/commands``. В onefile-сборке этих файлов на диске
    нет, поэтому команда импортируется напрямую и передаётся объектом.
    """
    from django.core.management import call_command
    from django.core.management.commands.migrate import Command as MigrateCommand

    # Имя команды не передаётся: при вызове с объектом команды первая
    # позиционная строка была бы воспринята как метка приложения
    # («No installed app with label 'migrate'»).
    call_command(MigrateCommand(), interactive=False, verbosity=1)


def _open_browser_later(url: str, delay: float = 1.5) -> None:
    """Открывает браузер через небольшую паузу, не блокируя сервер.

    :param url: адрес интерфейса.
    :param delay: задержка перед открытием, сек.
    """

    def _open() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 - отсутствие браузера не критично
            pass

    threading.Thread(target=_open, daemon=True).start()


def main(argv: list[str] | None = None) -> int:
    """Запускает сервис и блокируется до остановки пользователем.

    :param argv: аргументы командной строки (по умолчанию ``sys.argv[1:]``).
    :return: код возврата процесса.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    import django

    django.setup()

    from django.conf import settings

    print("=" * 62)
    print(" Avito Parser — сервис отслеживания количества объявлений")
    print("=" * 62)
    print(f" Данные и настройки: {settings.DATA_DIR}")

    try:
        run_migrations()
    except Exception as exc:  # noqa: BLE001 - показываем причину пользователю
        print(f"\n[ОШИБКА] Не удалось подготовить базу данных: {exc}")
        input("\nНажмите Enter, чтобы закрыть окно...")
        return 1

    port = pick_port(args.host, args.port)
    url = f"http://{args.host}:{port}"

    print(f" Интерфейс:          {url}")
    print(f" Документация API:   {url}/api/v1/docs/")
    print("\n Окно закрывать нельзя — оно и есть сервер.")
    print(" Для остановки нажмите Ctrl+C или закройте это окно.")
    print("=" * 62 + "\n")

    if not args.no_browser:
        _open_browser_later(url)

    from waitress import serve

    from parsing_project.wsgi import application

    # Планировщик восстанавливает задачи при первом запросе (см. apps.py),
    # поэтому дополнительный прогрев не нужен.
    try:
        serve(application, host=args.host, port=port, threads=8, _quiet=True)
    except KeyboardInterrupt:
        print("\nОстановка сервиса...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
