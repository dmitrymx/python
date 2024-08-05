import time
import os
from playwright.sync_api import sync_playwright
import sys
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import logging
import re
import psutil
import requests
import random
import string
from selenium.common.exceptions import TimeoutException

# API 1secmail
API = 'https://www.1secmail.com/api/v1/'
domainList = ['1secmail.com', '1secmail.net', '1secmail.org']

# Объявление глобальных переменных
successful_subscriptions = 0
failed_subscriptions = 0
successful_views = 0
failed_views = 0

# Настройка логирования по умолчанию
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def close_chrome_instances():
    """Закрывает все запущенные экземпляры Chrome, Chrome Driver, Undetected Chrome."""
    closed_chrome = 0
    closed_chromedriver = 0
    closed_undetected = 0

    # Получаем список всех запущенных процессов
    for process in psutil.process_iter():
        # Проверяем, является ли процесс Chrome или chromedriver
        if 'chrome.exe' in process.name() or 'chromedriver.exe' in process.name() or 'uc.exe' in process.name():
            if 'chrome.exe' in process.name():
                closed_chrome += 1
            elif 'chromedriver.exe' in process.name():
                closed_chromedriver += 1
            elif 'uc.exe' in process.name():
                closed_undetected += 1

            # Проверяем, существует ли процесс
            if process.is_running():
                # Закрываем процесс
                process.terminate()
                # Добавьте небольшую паузу (например, 0.5 секунды)
                time.sleep(0.5)

    logging.info(f"Закрыто {closed_chrome} экземпляров Chrome.exe.")
    logging.info(f"Закрыто {closed_chromedriver} экземпляров chromedriver.exe.")
    logging.info(f"Закрыто {closed_undetected} экземпляров Undetected Chromedriver.exe.")
def generate_random_mailbox():
    """Generates a random email address from 1secmail."""
    global domain
    domain = random.choice(domainList)
    username = generateUserName()  
    email_address = f"{username}@{domain}"
    try:
        # Ваш код для запроса к API 1secmail
        # ...
        return email_address 
    except Exception as e:
        logging.error(f"Ошибка при получении email-адреса: {e}")
        return None

def generateUserName():
    name = string.ascii_lowercase + string.digits
    username = ''.join(random.choice(name) for i in range(10))
    return username

def split_email(email):
    """Splits an email address into its login and domain parts."""
    parts = email.split('@')
    return parts[0], parts[1]

def check_mail(login_email, domain):
    """Checks for a new message in the 1secmail inbox."""
    reqLink = f'{API}?action=getMessages&login={login_email}&domain={domain}'
    try:
        req = requests.get(reqLink).json()
        length = len(req)
        if length > 0:
            message_id = req[0]['id']  # Берем ID первого письма
            return message_id
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении сообщений: {e}")
        return None

def get_auth_code(login_email, domain, message_id):
    """Retrieves the auth code from a 1secmail message."""
    msgRead = f'{API}?action=readMessage&login={login_email}&domain={domain}&id={message_id}'
    try:
        req = requests.get(msgRead).json()
        for k, v in req.items():
            if k == 'textBody':
                match = re.search(r'(\d{6})', v)  # Изменил регулярное выражение
                if match:
                    return match.group(1)
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении сообщения: {e}")
        return None

def login(driver, email):
    """Logs into the Nuum website."""
    logging.info("Открываем сайт https://nuum.ru/")
    driver.get("https://nuum.ru/")

    logging.info("Находим и последовательно нажимаем кнопки с задержкой в 3 секунды")
    login_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.brand-btn.small"))
    )
    login_button.click()
    time.sleep(3)

    logging.info("Находим и нажимаем кнопку 'Почта'")
    for i in range(3):  # Попробуем найти элемент 3 раза
        try:
            email_tab = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='tab'].label.full-width:nth-child(2)"))
            )
            email_tab.click()
            time.sleep(3)
            break  # Выходим из цикла, если элемент найден
        except TimeoutException:
            logging.warning("Элемент не найден. Повторная попытка.")

    # Если элемент не найден после 3 попыток, вызываем исключение
    if i == 2:
        raise Exception("Элемент не найден после 3 попыток.")

    logging.info("Вставляем email-адрес в поле ввода")
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
    )
    email_field.send_keys(email)

    logging.info("Нажимаем на кнопку 'Войти или зарегистрироваться'")
    submit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.brand-btn.large"))
    )
    submit_button.click()
    time.sleep(10)

    #  Добавить ожидание загрузки страницы
    wait_for_page_load(driver)

    return driver

#  Добавьте функцию для обработки ошибок при загрузке страницы
def wait_for_page_load(driver):
    """Ожидание полной загрузки страницы."""
    logging.info("Ожидаем полной загрузки страницы...")
    WebDriverWait(driver, 30).until(
        lambda driver: driver.execute_script("return document.readyState == 'complete'")
    )
    logging.info("Страница загружена.")

#  Добавьте функцию enter_code из второй части кода
def enter_code(driver, auth_code):
    """Ввод кода авторизации на Nuum."""
    logging.info("Ожидание появления поля для ввода кода")
    otp_inputs = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input.otp-input"))
    )
    
    logging.info(f"Ввод кода авторизации: {auth_code}")
    for i, digit in enumerate(auth_code):
        otp_inputs[i].send_keys(digit)

    logging.info("Нажимаем кнопку 'Войти'")
    submit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.brand-btn.large"))
    )
    submit_button.click()
    time.sleep(5)

    return True

def update_password(driver):
    """Updates the password on the Nuum website."""
    logging.info("Переходим на страницу https://nuum.ru/settings/security")
    driver.get("https://nuum.ru/settings/security")
    time.sleep(10)

    logging.info("Вводим новый пароль 'nirvana23' по полям")
    password_fields = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='password']"))
    )
    password_fields[0].send_keys("nirvana23")
    time.sleep(3)
    password_fields[1].send_keys("nirvana23")
    time.sleep(3)

    # После ввода пароля ставим фокус на второе поле ввода
    password_fields[1].click()

    # Нажимаем TAB два раза и ENTER с задержкой
    action_chains = ActionChains(driver)
    action_chains.send_keys(Keys.TAB)
    action_chains.perform()
    time.sleep(2)
    action_chains.send_keys(Keys.TAB)
    action_chains.perform()
    time.sleep(2)
    action_chains.send_keys(Keys.ENTER)
    action_chains.perform()
    time.sleep(5)

def write_to_file(email):
    """Saves the email address and password to a file."""
    with open("emailsonuum.txt", "a") as f:
        f.write(f"{email}:nirvana23\n")
    logging.info("Email-адрес и пароль сохранены в файл emailsonuum.txt")

def subscribe_to_channel(driver, channel_url):
    """Подписывается на канал."""
    logging.info(f"Переходим на страницу {channel_url}")
    driver.get(channel_url)
    time.sleep(10)

    logging.info("Находим и кликаем на кнопку 'Подписаться'")
    subscribe_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "app-follow-btn button.secondary-btn.small"))
    )
    subscribe_button.click()
    time.sleep(4)
    #  Добавить проверку на подписку

def generate_account(save_credentials, channel_url):
    """Generates an account, logs in, subscribes, and updates password (if requested)."""
    global successful_subscriptions, failed_subscriptions  # Делаем переменные глобальными

    try:
        # Закрываем все запущенные процессы Chrome в начале
        close_chrome_instances()

        #  Определяем новый User Agent
        agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"

        #  Устанавливаем опции Chrome
        opts = uc.ChromeOptions()
        opts.add_argument(f"user-agent={agent}")
        opts.add_argument("--incognito")  # Запускаем браузер в инкогнито-режиме
        opts.add_argument("--disable-popup-blocking")  # Отключаем блокировку всплывающих окон
        opts.add_argument("--disable-images")  # Отключаем загрузку изображений
        opts.add_argument("--headless")  #  Запускаем браузер в режиме headless - убрали headless

        #  Создаем экземпляр WebDriver
        driver = uc.Chrome(options=opts)

        #  Генерация случайного email-адреса
        email = generate_random_mailbox()
        logging.info(f"Generated email: {email}")

        #  Разделение email-адреса на логин и домен
        if email is None:
            logging.warning("Не удалось получить email-адрес. Пропускаем.")
            driver.quit()
            return False
        login_email, domain = split_email(email)
        logging.info(f"Логин: {login_email}")
        logging.info(f"Домен: {domain}")

        #  Логин на сайт
        driver = login(driver, email) 

        #  Получение кода авторизации из письма
        message_id = None
        attempts = 0
        max_attempts = 5
        while message_id is None and attempts < max_attempts:  # Ожидаем, пока не получим письмо
            message_id = check_mail(login_email, domain)
            logging.info(f"Message ID: {message_id}")
            attempts += 1
            time.sleep(2)

        if message_id is None:
            logging.warning("Письмо не получено после 5 попыток. Пропускаем.")
            driver.quit()
            failed_subscriptions += 1 # Увеличиваем failed_subscriptions, если письмо не получено
            return False  # Возвращаем False, чтобы не увеличивать successful_subscriptions

        auth_code = get_auth_code(login_email, domain, message_id)
        if auth_code:
            logging.info(f"Код авторизации: {auth_code}")
            # Ввод кода в поле code_field
            if enter_code(driver, auth_code):
                if save_credentials.lower() == "да":
                    update_password(driver)
                    write_to_file(email)
                    #  Переход на страницу канала
                    driver.get(channel_url)
                    time.sleep(10)

                    #  Ищем и нажимаем кнопку "Подписаться"
                    subscribe_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "app-follow-btn button.secondary-btn.small"))
                    )
                    subscribe_button.click()
                    time.sleep(4)
                else:
                    #  Переход на страницу канала
                    driver.get(channel_url)
                    time.sleep(10)

                    #  Ищем и нажимаем кнопку "Подписаться"
                    subscribe_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "app-follow-btn button.secondary-btn.small"))
                    )
                    subscribe_button.click()
                    time.sleep(4)

                #  Проверка на успешную подписку
                #  Ищем элемент с текстом "Вы подписаны"
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Вы подписаны')]"))
                    )
                    logging.info(f"Успешно подписались на канал {channel_url}.")
                    successful_subscriptions += 1  # Увеличиваем successful_subscriptions только если подписка прошла успешно
                except TimeoutException:
                    logging.warning(f"Подписка на канал {channel_url} не подтверждена.")
                    failed_subscriptions += 1  # Увеличиваем failed_subscriptions, если подписка не прошла

            #  Закрываем браузер
            driver.quit()
            return True
        else:
            logging.warning("Код авторизации не найден. Пропускаем.")
            driver.quit()
            failed_subscriptions += 1 # Увеличиваем failed_subscriptions при ошибке
            return False
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        driver.quit()
        failed_subscriptions += 1 # Увеличиваем failed_subscriptions при ошибке
        return False

def view_and_like_video(driver, video_url, like=True):
    """Смотрим видео и ставим лайк (если like=True)."""
    global successful_views, failed_views

    try:
        logging.info(f"Переходим на видео: {video_url}")
        driver.get(video_url)
        time.sleep(10)  # Ждем загрузки видео

        # Проверяем, что видео действительно загрузилось (например, ищем кнопку лайка)
        like_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.reactions__button.button.button--transparent"))
        )

        # Смотрим видео от 15 до 30 секунд
        logging.info("Смотрим видео от 15 до 30 секунд.")
        time.sleep(random.randint(15, 30))

        # Ставим лайк, если нужно
        if like:
            logging.info("Ставим лайк на видео.")
            like_button.click()
            time.sleep(2)

        # Проверяем, что лайк поставлен (например, проверяем наличие значка сердечка)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.reactions__button.button.button--transparent svg[data-inlinesvg='icons-heart-size-24-style-regular']"))
            )
            logging.info("Лайк поставлен успешно.")
            successful_views += 1
        except TimeoutException:
            logging.warning("Лайк не поставлен.")
            failed_views += 1

        return True

    except Exception as e:
        logging.error(f"Ошибка при просмотре видео: {e}")
        return False

def main():
    global successful_subscriptions, failed_subscriptions, successful_views, failed_views  # Делаем переменные глобальными

    # Вводим данные только один раз
    action = input("Выберите действие (подписка/просмотр): ").lower()
    video_url = input("Введите ссылку на видео: ")
    like = input("Ставить лайк? (да/нет): ").lower() == 'да'
    channel_url = input("Введите ссылку на канал для подписки (необязательно): ")
    max_views = input("Введите максимальное количество просмотров (пусто для бесконечного цикла): ")
    if max_views:
        max_views = int(max_views)

    #  Определяем новый User Agent
    agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"

    #  Устанавливаем опции Chrome
    opts = uc.ChromeOptions()
    opts.add_argument(f"user-agent={agent}")
    opts.add_argument("--incognito")  # Запускаем браузер в инкогнито-режиме
    opts.add_argument("--disable-popup-blocking")  # Отключаем блокировку всплывающих окон
    opts.add_argument("--disable-images")  # Отключаем загрузку изображений
    opts.add_argument("--headless")  #  Запускаем браузер в режиме headless - убрали headless

    while True:
        try:
            if action == "подписка":
                channel_url = input("Введите ссылку на канал: ")
                logging.info(f"Ссылка на канал: {channel_url}")

                save_credentials = input("Сохранить логин и пароль в файл? (да/нет): ")

                log_level = input("Выберите уровень логирования (подробный/простой): ").lower()
                
                # Настройка уровня логирования
                if log_level == "подробный":
                    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
                elif log_level == "простой":
                    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
                else:
                    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
                    logging.warning("Неверный уровень логирования. Используется стандартный уровень.")

                max_subscriptions = input("Введите максимальное количество подписок (пусто для бесконечного цикла): ")
                if max_subscriptions:
                    max_subscriptions = int(max_subscriptions)

                while True:
                    if generate_account(save_credentials, channel_url):
                        # Увеличиваем успешные подписки только после проверки на наличие кнопки "Подписаться"
                        print(f"Успешных подписок: {successful_subscriptions}")
                        print(f"Неудачных подписок: {failed_subscriptions}")

                    if max_subscriptions and successful_subscriptions >= max_subscriptions:
                        print("Достигнуто максимальное количество подписок. Завершение работы.")
                        close_chrome_instances()  # Закрываем все процессы Chrome после завершения
                        break  # Выход из цикла

            elif action == "просмотр":
                while True:
                    #  Создаем новый объект ChromeOptions
                    opts = uc.ChromeOptions()
                    opts.add_argument(f"user-agent={agent}")
                    opts.add_argument("--incognito")  # Запускаем браузер в инкогнито-режиме
                    opts.add_argument("--disable-popup-blocking")  # Отключаем блокировку всплывающих окон
                    opts.add_argument("--disable-images")  # Отключаем загрузку изображений
                    opts.add_argument("--headless")  #  Запускаем браузер в режиме headless - убрали headless

                    #  Создаем экземпляр WebDriver
                    driver = uc.Chrome(options=opts)

                    #  Генерация случайного email-адреса
                    email = generate_random_mailbox()
                    logging.info(f"Generated email: {email}")

                    #  Разделение email-адреса на логин и домен
                    if email is None:
                        logging.warning("Не удалось получить email-адрес. Пропускаем.")
                        driver.quit()
                        continue
                    login_email, domain = split_email(email)
                    logging.info(f"Логин: {login_email}")
                    logging.info(f"Домен: {domain}")

                    #  Логин на сайт
                    driver = login(driver, email) 

                    #  Получение кода авторизации из письма
                    message_id = None
                    attempts = 0
                    max_attempts = 5
                    while message_id is None and attempts < max_attempts:  # Ожидаем, пока не получим письмо
                        message_id = check_mail(login_email, domain)
                        logging.info(f"Message ID: {message_id}")
                        attempts += 1
                        time.sleep(2)

                    if message_id is None:
                        logging.warning("Письмо не получено после 5 попыток. Пропускаем.")
                        driver.quit()
                        continue

                    auth_code = get_auth_code(login_email, domain, message_id)
                    if auth_code:
                        logging.info(f"Код авторизации: {auth_code}")
                        # Ввод кода в поле code_field
                        if enter_code(driver, auth_code):
                            #  Подписаться на канал (необязательно)
                            if channel_url:
                                subscribe_to_channel(driver, channel_url)

                            #  Перейти на видео 
                            if view_and_like_video(driver, video_url, like):
                                print(f"Успешных просмотров: {successful_views}")
                                print(f"Неудачных просмотров: {failed_views}")

                                # Закрываем браузеры после каждого успешного просмотра
                                close_chrome_instances()

                                if max_views and successful_views >= max_views:
                                    print("Достигнуто максимальное количество просмотров. Завершение работы.")
                                    break  # Выход из цикла
                        else:
                            driver.quit()
                            failed_views += 1
                    else:
                        driver.quit()
                        failed_views += 1
        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")
            logging.info("Перезапускаем скрипт...")
            close_chrome_instances() # Закрываем все браузеры перед перезапуском
            time.sleep(5) # Добавьте небольшую паузу перед перезапуском

if __name__ == "__main__":
    main()
