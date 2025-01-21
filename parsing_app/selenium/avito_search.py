from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

from selenium.webdriver.support.ui import WebDriverWait

options = webdriver.ChromeOptions()

# options.add_argument("--headless")  # Включение headless-режима
options.add_argument("--disable-gpu")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--disable-javascript")  # Отключение JavaScript
# options.add_argument("--blink-settings=imagesEnabled=false")  # Отключение изображений
city = "краснодар"
# browser = webdriver.Chrome(options=options)
with webdriver.Chrome(options=options) as browser:
    browser.get("https://avito.ru")

    # ------------------------------ Выбор города -------------------------------------
    # выбор города
    browser.find_element(By.CSS_SELECTOR, "span.buyer-location-nev1ty").click()
    time.sleep(0.1)

    # поле ввода города
    input_city = browser.find_element(
        By.CSS_SELECTOR, "input.styles-module-searchInput-fm9ey"
    )

    time.sleep(0.1)
    input_city.click()  # перейти к полю
    time.sleep(0.1)
    input_city.clear()  # очистить
    time.sleep(0.1)
    for i in city:
        input_city.send_keys(i)
        time.sleep(0.4)
    # input_city.send_keys(city)  # город
    time.sleep(2)

    # input_city.send_keys(Keys.ENTER)

    button = browser.find_element(
        By.CSS_SELECTOR,
        "button.styles-module-root-hUB0x.styles-module-root_size_s-OErXY.styles-module-root_preset_primary-BrO4Z",
    )
    # button = browser.find_element(
    #     By.CSS_SELECTOR, "button[data-marker='popup-location/save-button']"
    # )
    browser.execute_script("arguments[0].click();", button)
    time.sleep(2)
    # ---------------------------------------------------------------------------------

    input_elem = browser.find_element(
        By.CSS_SELECTOR, "input.styles-module-input-rA1dB"
    )  # поле поиска

    input_elem.send_keys("Samsung")  # объект поиска

    button = browser.find_element(
        By.CLASS_NAME, "buyer-location-xp6ezn"
    ).click()  # start поиск

    time.sleep(3)
    total = browser.find_element(
        By.CSS_SELECTOR, "span[data-marker='page-title/count']"
    ).text  # получить
    total = int(
        total.replace(" объявлений", "").replace(" ", "")
    )  # убрать пробелы и заменить на число
    print(f"Всего объявлений: {total}")
