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
        self.options = Options()
        # Remove headless mode
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(options=self.options)

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def manual_login(self, credentials_file, max_retries=3):
        try:
            with open(credentials_file) as f:
                creds = json.load(f)

            self.driver.get("https://twitter.com/i/flow/login")
            time.sleep(3)

            for attempt in range(max_retries):
                try:
                    # Find and fill username
                    logging.info("Waiting for username field...")
                    username_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'input[autocomplete="username"]')
                        )
                    )
                    username_input.clear()
                    username_input.send_keys(creds["username"])
                    username_input.send_keys(
                        Keys.ENTER
                    )  # Use Enter instead of Next button
                    time.sleep(2)

                    # Find and fill password
                    logging.info("Waiting for password field...")
                    password_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'input[type="password"]')
                        )
                    )
                    password_input.clear()
                    password_input.send_keys(creds["password"])
                    password_input.send_keys(
                        Keys.ENTER
                    )  # Use Enter instead of Login button
                    time.sleep(5)

                    # Verify login
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: "twitter.com/home" in driver.current_url
                    )

                    logging.info("Login successful!")
                    self.save_cookies()
                    return True

                except Exception as e:
                    logging.warning(f"Login attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
                    continue

            return False

        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            return False

    def save_cookies(self):
        cookie_path = os.path.join("data", "cookies", "twitter_cookies.pkl")
        with open(cookie_path, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)
        logging.info("Saved new cookies")

    def load_cookies(self, cookie_file: str):
        try:
            # Load Twitter homepage first
            logging.info("Loading Twitter homepage...")
            self.driver.get("https://twitter.com")
            time.sleep(3)

            # Load and apply cookies
            logging.info("Loading cookies from file...")
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                        logging.info(f"Added cookie: {cookie.get('name')}")
                    except Exception as e:
                        logging.warning(
                            f"Failed to add cookie {cookie.get('name')}: {e}"
                        )

            # Refresh and verify auth state
            logging.info("Verifying authentication...")
            self.driver.get("https://twitter.com/home")
            time.sleep(3)

            # Check if we're actually logged in by looking for logout button
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'a[data-testid="AppTabBar_Profile_Link"]')
                    )
                )
                logging.info("Successfully authenticated with cookies")
                return True
            except:
                logging.error("Cookie authentication failed")
                return False

        except Exception as e:
            logging.error(f"Error loading cookies: {e}")
            return False

    def close(self):
        self.driver.close()
