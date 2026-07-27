"""Пути проекта для обычного запуска и для запуска из собранного .exe.

При сборке PyInstaller в режиме ``--onefile`` код и шаблоны распаковываются во
временный каталог (``sys._MEIPASS``), который удаляется после выхода. Класть
туда базу данных, ``.env`` или ``proxies.txt`` нельзя — данные пропадут после
закрытия программы, а сам каталог доступен только на чтение.

Поэтому различаются два корня:

* :func:`resource_dir` — где лежат упакованные ресурсы (шаблоны, статика, код);
* :func:`data_dir` — куда можно писать (БД, логи) и откуда читать
  пользовательские настройки (``.env``, ``proxies.txt``). Для .exe это каталог
  рядом с самим .exe, для обычного запуска — корень репозитория.
"""

from pathlib import Path
import os
import sys

# Корень репозитория при обычном запуске: ../ от этого файла.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    """Сообщает, выполняется ли код внутри собранного PyInstaller приложения.

    :return: ``True``, если приложение запущено из .exe.
    """
    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """Возвращает каталог с упакованными ресурсами (только чтение).

    :return: ``sys._MEIPASS`` для .exe, иначе корень репозитория.
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return _PROJECT_ROOT


def data_dir() -> Path:
    """Возвращает каталог для пользовательских данных (чтение и запись).

    Для .exe это папка рядом с исполняемым файлом: там пользователь держит
    ``.env``/``proxies.txt`` и там же создаётся ``db.sqlite3``. Путь можно
    переопределить переменной окружения ``AVITO_DATA_DIR`` (удобно, если .exe
    лежит в ``Program Files``, куда нет прав на запись).

    :return: существующий каталог для данных.
    """
    override = os.environ.get("AVITO_DATA_DIR", "").strip()
    if override:
        path = Path(override).expanduser()
    elif is_frozen():
        path = Path(sys.executable).resolve().parent
    else:
        path = _PROJECT_ROOT

    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Каталог рядом с .exe может быть недоступен для записи
        # (Program Files) — уходим в профиль пользователя.
        path = Path.home() / "AvitoParser"
        path.mkdir(parents=True, exist_ok=True)
    return path
