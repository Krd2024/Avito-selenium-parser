Тестовое задание для стажера в Market Intelligence.

Задача:
Необходимо реализовать сервис, позволяющий следить за изменением количества объявлений в Авито по определённому поисковому запросу и региону.


UI не нужен, достаточно сделать JSON API сервис.

Для написание сервиса можно использовать FastAPI или любой другой фреймворк.

Метод /add Должен принимать поисковую фразу и регион, регистрировать их в системе. Возвращать id этой пары.
Метод /stat Принимает на вход id связки поисковая фраза + регион и интервал, за который нужно вывести счётчики. Возвращает счётчики и соответствующие им временные метки (timestamp).
Частота опроса = 1 раз в час  для каждого id

Требования:
Язык программирования: Python 3.7/3.8
Использование Docker, сервис должен запускаться с помощью docker-compose up.
Требований к используемым технологиям нет.
Код должен соответствовать PEP, необходимо использование type hints, к публичным методам должна быть написана документация.

Чтобы получить число объявлений, можно:
парсить web-страницу объявления (xpath, css-селекторы)
самостоятельно проанализировать трафик на мобильных приложениях или мобильном сайте и выяснить какой там API для получения информации об объявлении (это будет круто!)

Усложнения:
Написаны тесты (постарайтесь достичь покрытия в 70% и больше). Вы можете использовать pytest или любую другую библиотеку для тестирования.

Сервис асинхронно обрабатывает запросы.
Данные сервиса хранятся во внешнем хранилище, запуск которого также описан в docker-compose. Мы рекомендуем использовать MongoDB или Postgres, но Вы можете использовать любую подходящую базу.

По каждому id также собираются топ 5 объявлений. На их получение есть отдельная ручка, архитектуру продумайте самостоятельно

