import os
from datetime import timedelta

import redis
from bs4 import BeautifulSoup as BS
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver

from dotenv import load_dotenv

load_dotenv()

url = "https://www.kufar.by/l/r~minsk/kompyuternaya-tehnika"

login = os.getenv("PROXY_LOGIN")
password = os.getenv("PROXY_PASSWORD")


def handler():
    client_redis = _get_redis_client()
    options = _get_options_for_chrome_webdriver()
    caps = _get_capabilities()
    proxy_options = _get_proxy_options()
    page_source = _get_page_source_with_webdriver(options=options, caps=caps,
                                                  proxy_options=proxy_options)
    fresh_news = _parsing_new_links(text=page_source, client_redis=client_redis)
    return fresh_news


def _get_proxy_options() -> dict:
    proxy_options = {
        "proxy": {
            "https": f"http://{login}:{password}@45.143.245.225:8000"
        }
    }
    return proxy_options


def _get_redis_client() -> redis.StrictRedis:
    client_redis = redis.StrictRedis(
        host='redis-17704.c269.eu-west-1-3.ec2.cloud.redislabs.com',
        port=17704, db=0,
        password='W111LReek1K6mj0feYLAjkyhjKANk89h')
    return client_redis


def _get_capabilities() -> DesiredCapabilities:
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"
    return caps


def _get_options_for_chrome_webdriver() -> Options:
    options = webdriver.ChromeOptions()
    options.add_argument("general.useragent.override")
    options.add_argument(" Chrome/102.0.5005.115 Mobile")
    options.add_argument("--headless")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('start-maximized')
    options.add_argument('--ignore-certificate-errors-spki-list')

    return options


def _get_page_source_with_webdriver(options: Options, caps: DesiredCapabilities or None,
                                    proxy_options: dict):
    path_to_driver = os.getenv("PATH_TO_DRIVER")
    with webdriver.Chrome(executable_path=path_to_driver, options=options,
                          seleniumwire_options=proxy_options, desired_capabilities=caps) as \
            driver:
        driver.get("https://www.kufar.by/l/r~minsk/sistemnye-bloki")
        WebDriverWait(driver, 25).until(EC.presence_of_all_elements_located(
            (By.XPATH, '//section')))
        res = driver.page_source
    return res


def _parsing_new_links(text, client_redis):
    try:
        fresh_news = {}
        html = BS(text, 'html.parser')
        items = html.find_all("section")
        for item in items:
            _id = item.find('a').get('href').split('/')[-1]
            if bytes(_id, encoding='utf-8') in client_redis.keys():
                continue
            else:
                link = item.find('a').get('href')
                _id = link.split('/')[-1]
                fresh_news[_id] = {
                    'link': link
                }
                client_redis.setex(_id, time=timedelta(days=2), value=link)
        return fresh_news
    except Exception as e:
        print(e)
    finally:
        client_redis.quit()


def check_new_products():
    fresh_news = handler()
    return fresh_news


if __name__ == '__main__':
    handler()
