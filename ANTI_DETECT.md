# Анти-детект меры для парсера Авито

## Обзор

Модуль `anti_detect.py` содержит меры для избежания блокировки со стороны Авито при автоматическом парсинге.

## Реализованные меры

### 1. Ротация User-Agent

**Проблема:** Использование одного и того же User-Agent для всех запросов легко обнаруживается антибот-системами.

**Решение:** Пул из 10+ реальных User-Agent'ов (Chrome, Firefox, Edge, Safari для Windows и macOS) с случайным выбором при каждом запуске браузера.

**Код:**
```python
user_agent = get_random_user_agent()
options.add_argument(f"user-agent={user_agent}")
```

### 2. Эмуляция поведения пользователя

**Проблема:** Мгновенные действия без задержек характерны для ботов, а не для людей.

**Решение:** Случайные задержки между действиями:
- Перед навигацией: 1-3 секунды
- После загрузки страницы: 2-4 секунды
- Перед кликом по переключателю: 1-2.5 секунды
- После клика: 5-10 секунд (AJAX-обновление)

**Код:**
```python
human_like_delay(1.0, 3.0)  # Случайная задержка от 1 до 3 секунд
```

### 3. Движения мыши

**Проблема:** Отсутствие движений мыши - признак автоматизации.

**Решение:** Случайные движения мыши по странице перед важными действиями:
- Случайные смещения курсора
- Плавные переходы к элементам
- Паузы перед кликами

**Код:**
```python
from selenium.webdriver.common.action_chains import ActionChains
actions = ActionChains(browser)
actions.move_to_element(toggle)
actions.pause(0.5)
actions.perform()
```

### 4. Скролл страницы

**Проблема:** Отсутствие скролла - человек обычно прокручивает страницу.

**Решение:** Случайные скроллы вверх/вниз с различной амплитудой (100-500px).

**Код:**
```python
scroll_amount = random.randint(100, 500)
browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
```

### 5. Отключение признаков автоматизации

**Проблема:** Selenium оставляет следы, по которым его можно обнаружить.

**Решение:** Отключение автоматизационных флагов:
```python
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
```

### 6. Длительное ожидание после критических действий

**Проблема:** Мгновенное чтение данных после клика по фильтру выглядит подозрительно.

**Решение:** После клика по переключателю "Сначала из города":
- Ждём 5-10 секунд с эмуляцией поведения (скроллы, движения мыши)
- Ждём до 15 секунд появления обновлённого счётчика
- Даём 2-4 секунды на полное обновление DOM

**Код:**
```python
wait_after_critical_action(browser, min_wait=5.0, max_wait=10.0)
```

## Архитектура

```
parsing_app/selenium/
├── anti_detect.py          # Анти-детект меры
│   ├── USER_AGENTS         # Пул User-Agent'ов
│   ├── get_random_user_agent()
│   ├── human_like_delay()
│   ├── random_scroll()
│   ├── random_mouse_movement()
│   ├── simulate_human_behavior()
│   └── wait_after_critical_action()
└── avito_search.py         # Основной парсер (использует anti_detect)
```

## Использование

Все анти-детект меры интегрированы в `avito_search.py` и применяются автоматически:

```python
# В build_options()
user_agent = get_random_user_agent()
options.add_argument(f"user-agent={user_agent}")

# В get_browser()
human_like_delay(1.0, 3.0)
simulate_human_behavior(browser, pre_action=False)

# В _click_local_priority_toggle()
simulate_human_behavior(browser, pre_action=True)
wait_after_critical_action(browser, min_wait=5.0, max_wait=10.0)
```

## Результаты

До применения анти-детект мер:
- ❌ Блокировка после 1-2 запросов
- ❌ Капча после переключения фильтра
- ❌ Подозрительная активность

После применения:
- ✅ Стабильная работа без блокировок
- ✅ Нет капчи
- ✅ Естественное поведение

## Настройка

Для изменения параметров редактируйте `anti_detect.py`:

```python
# Увеличить пул User-Agent'ов
USER_AGENTS = [
    # ... добавьте больше User-Agent'ов
]

# Изменить диапазон задержек
human_like_delay(min_seconds=2.0, max_seconds=5.0)

# Изменить время ожидания после критического действия
wait_after_critical_action(browser, min_wait=8.0, max_wait=15.0)
```

## Предупреждения

1. **Не злоупотребляйте** - делайте паузы между запросами (рекомендуется 30-60 секунд)
2. **Используйте прокси** - для массового парсинга необходима ротация IP
3. **Соблюдайте robots.txt** - уважайте правила сайта
4. **Ограничьте частоту** - не более 1 запроса в минуту для одного IP

## Лицензия

Этот код предназначен для образовательных целей. Используйте ответственно.
