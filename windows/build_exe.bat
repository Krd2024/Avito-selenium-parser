@echo off
chcp 65001 >nul
REM ============================================================
REM  Сборка AvitoParser.exe (запускать на Windows)
REM  PyInstaller не умеет кросс-компиляцию: .exe собирается
REM  только на Windows.
REM ============================================================
setlocal

cd /d "%~dp0\.."

echo.
echo [1/5] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.10-3.12 с python.org
    echo          и отметьте "Add python.exe to PATH".
    pause
    exit /b 1
)
python --version

echo.
echo [2/5] Создание виртуального окружения build_venv...
if not exist build_venv (
    python -m venv build_venv || (echo [ОШИБКА] Не удалось создать venv & pause & exit /b 1)
)

echo.
echo [3/5] Установка зависимостей...
call build_venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || (echo [ОШИБКА] Установка зависимостей & pause & exit /b 1)
pip install -r windows\requirements-build.txt || (echo [ОШИБКА] Установка сборочных зависимостей & pause & exit /b 1)

echo.
echo [4/5] Сборка статики...
python manage.py collectstatic --noinput --clear
if errorlevel 1 echo [ПРЕДУПРЕЖДЕНИЕ] collectstatic завершился с ошибкой, продолжаем.

echo.
echo [5/5] Сборка исполняемого файла...
pyinstaller windows\avito_parser.spec --noconfirm --clean || (echo [ОШИБКА] Сборка не удалась & pause & exit /b 1)

echo.
echo ============================================================
echo  Готово: dist\AvitoParser.exe
echo  Скопируйте .exe в любую папку и запустите двойным кликом.
echo ============================================================
pause
