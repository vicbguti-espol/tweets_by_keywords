from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import logging
import sys
import os
import json
import pickle
import time


class SearcherDriver:
    def __init__(self, executable_path):
        if executable_path is None:
            print(
                "[WARNING] No executable path provided. Searching for chromedriver in PATH"
            )

        self.driver = webdriver.Chrome(
            service=webdriver.ChromeService(executable_path=executable_path)
        )
        self.by_type = {"id": By.ID, "css": By.CSS_SELECTOR, "xpath": By.XPATH}

    def get(self, url):
        self.driver.get(url)

    def close(self):
        self.driver.close()

    def get_element_by(self, selector_type, selector, timeout=5):
        by_selector = self.by_type.get(selector_type)

        if by_selector is None:
            raise ValueError(
                f"Invalid selector type: {selector_type} - must be 'id', 'css', or 'xpath'"
            )

        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by_selector, selector))
        )

        if element is None:
            raise Exception(f"Element not found: {selector}")

        return element

    def get_elements_by(self, selector_type, selector, timeout=5):
        by_selector = self.by_type.get(selector_type)

        if by_selector is None:
            raise ValueError(
                f"Invalid selector type: {selector_type} - must be 'id', 'css', or 'xpath'"
            )

        elements = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located((by_selector, selector))
        )

        if elements is None:
            raise Exception(f"Elements not found: {selector}")

        return elements


class Browser:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.options = Options()
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(options=self.options)
        self.cookie_dir = os.path.join("data", "cookies")
        self.cookie_path = os.path.join(self.cookie_dir, "twitter_cookies.pkl")
        os.makedirs(self.cookie_dir, exist_ok=True)
        self.authenticate()

    def authenticate(self):
        logging.info("Starting authentication process...")
        if self.try_cookie_auth():
            return True
        return self.try_manual_auth()

    def try_cookie_auth(self):
        if not os.path.exists(self.cookie_path):
            return False

        try:
            self.driver.get("https://twitter.com")
            time.sleep(3)

            with open(self.cookie_path, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)

            self.driver.get("https://twitter.com/home")
            time.sleep(5)

            if self.is_logged_in():
                logging.info("Successfully authenticated with cookies")
                return True

            logging.info("Cookie authentication failed")
            os.remove(self.cookie_path)
            return False

        except Exception as e:
            logging.error(f"Cookie auth error: {e}")
            return False

    def try_manual_auth(self):
        credentials_path = os.path.join("config", "credentials.json")
        if not os.path.exists(credentials_path):
            raise Exception("No credentials file found")

        try:
            with open(credentials_path) as f:
                creds = json.load(f)

            self.driver.get("https://twitter.com/i/flow/login")
            time.sleep(5)

            # Enter username
            username = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[autocomplete="username"]')
                )
            )
            username.send_keys(creds["username"])
            username.send_keys(Keys.ENTER)
            time.sleep(3)

            # Enter password
            password = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[type="password"]')
                )
            )
            password.send_keys(creds["password"])
            password.send_keys(Keys.ENTER)
            time.sleep(5)

            if self.is_logged_in():
                logging.info("Manual login successful")
                self.save_cookies()
                return True

            logging.error("Manual login failed")
            return False

        except Exception as e:
            logging.error(f"Manual auth error: {e}")
            return False

    def is_logged_in(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'a[data-testid="AppTabBar_Home_Link"]')
                )
            )
            return True
        except:
            return False

    def save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookie_path, "wb") as f:
                pickle.dump(cookies, f)
            logging.info("Cookies saved successfully")
        except Exception as e:
            logging.error(f"Failed to save cookies: {e}")

    def close(self):
        self.driver.close()
