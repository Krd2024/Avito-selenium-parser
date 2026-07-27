# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-спецификация для сборки AvitoParser.exe.

Собирает Django-проект в один исполняемый файл. Особенности, из-за которых
обычная автоматическая сборка не работает и нужен явный spec:

* Django находит шаблоны, миграции и статику по файлам на диске — их надо
  положить в бандл вручную (``collect_data_files`` + templates приложения);
* management-команды, бэкенды БД и middleware импортируются по строковым
  именам, поэтому анализатор их не видит — они перечислены в hiddenimports;
* apscheduler ищет типы триггеров и исполнителей через entry points.

Сборка (из корня репозитория)::

    pyinstaller windows/avito_parser.spec --noconfirm
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# spec-файл выполняется с рабочим каталогом = корень проекта.
PROJECT_ROOT = Path(SPECPATH).resolve().parent

# collect_submodules импортирует модули, а часть из них (например,
# rest_framework.schemas) при импорте читает настройки Django и падает с
# ImproperlyConfigured, из-за чего зависимости молча не попадали в сборку.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parsing_project.settings")

datas = []
hiddenimports = []

# --- Шаблоны и статика проекта --------------------------------------------
datas.append((str(PROJECT_ROOT / "parsing_app" / "templates"), "parsing_app/templates"))

# --- Django: шаблоны админки, локали, статика, миграции контриб-приложений --
datas += collect_data_files("django", include_py_files=False)
# Management-команды — это .py-файлы, которые Django ищет перебором каталога.
# include_py_files=True обязателен: без него .py-файлы отбрасываются как код,
# и migrate/collectstatic не находятся в собранном .exe.
datas += collect_data_files(
    "django", includes=["**/management/commands/*.py"], include_py_files=True
)
datas += collect_data_files("rest_framework", include_py_files=False)
datas += collect_data_files("drf_spectacular", include_py_files=False)
datas += collect_data_files("django_apscheduler", include_py_files=False)
# Миграции django_apscheduler тоже .py — нужны, иначе migrate падает.
datas += collect_data_files(
    "django_apscheduler", includes=["**/migrations/*.py"], include_py_files=True
)
# Миграции самого проекта: Django ищет их файлами в каталоге.
datas.append(
    (str(PROJECT_ROOT / "parsing_app" / "migrations"), "parsing_app/migrations")
)

# --- Selenium Manager ------------------------------------------------------
# selenium 4.28 сам скачивает подходящий chromedriver, но делает это
# вспомогательным бинарником selenium-manager.exe внутри пакета. Без него
# в собранном .exe парсинг падает с "Unable to obtain driver".
datas += collect_data_files("selenium")

# --- Скрытые импорты -------------------------------------------------------
# Приложения проекта целиком: модели/вьюхи подтягиваются по строкам из settings.
hiddenimports += collect_submodules("parsing_app")
hiddenimports += collect_submodules("parsing_project")
hiddenimports += collect_submodules("django_apscheduler")
hiddenimports += collect_submodules("apscheduler")
hiddenimports += collect_submodules("rest_framework")
hiddenimports += collect_submodules("drf_spectacular")
hiddenimports += [
    # Ядро Django, загружаемое по строковым путям из settings.py.
    "django.contrib.admin.apps",
    "django.contrib.auth.apps",
    "django.contrib.contenttypes.apps",
    "django.contrib.sessions.apps",
    "django.contrib.messages.apps",
    "django.contrib.staticfiles.apps",
    "django.contrib.sessions.serializers",
    "django.contrib.messages.storage.fallback",
    "django.core.management.commands.migrate",
    "django.core.management.commands.collectstatic",
    "django.db.backends.sqlite3",
    "django.db.backends.sqlite3.base",
    "django.db.backends.mysql",
    "django.db.backends.mysql.base",
    "django.template.loaders.app_directories",
    "django.template.loaders.filesystem",
    # Драйвер MySQL (используется, если пользователь укажет DB_ENGINE=mysql).
    "pymysql",
    # Веб-сервер и статика.
    "waitress",
    "whitenoise",
    "whitenoise.middleware",
    # Прочие рантайм-зависимости.
    "selenium",
    "loguru",
    "decouple",
]

a = Analysis(
    [str(PROJECT_ROOT / "run_app.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Тяжёлые научные пакеты в проект не входят — исключаем на случай,
    # если они окажутся в окружении сборки и раздуют .exe.
    excludes=["tkinter", "numpy", "pandas", "matplotlib", "PyQt5", "PySide2"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AvitoParser",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Консоль нужна: в ней видны адрес интерфейса, логи парсинга и ошибки.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
