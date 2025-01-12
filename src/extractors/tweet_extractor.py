from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.models.tweet import Tweet
import logging
import time
import urllib.parse
from datetime import datetime


class TweetExtractor:
    def extract_username(self, tweet_element):
        try:
            # Get username with @ symbol from second span
            username = tweet_element.find_element(
                By.CSS_SELECTOR,
                '[data-testid="User-Name"] div.css-175oi2r.r-1ez5h0i div.r-1wbh5a2 span',
            ).text

            logging.debug(f"Raw username found: {username}")

            if username and "@" in username:
                return username
            else:
                logging.warning(f"Invalid username format: {username}")
                return None

        except Exception as e:
            logging.error(f"Error extracting username: {e}")
            return None

    def extract_tweet_data(self, tweet_element):
        try:
            # Get username
            username = self.extract_username(tweet_element)
            if not username:
                return None

            # Get tweet URL and timestamp
            tweet_link = tweet_element.find_element(
                By.CSS_SELECTOR,
                '[data-testid="User-Name"] div.css-175oi2r.r-18u37iz.r-1q142lx a[role="link"]',
            )
            tweet_url = f"https://twitter.com{tweet_link.get_attribute('href')}"

            # Get original timestamp
            timestamp = tweet_element.find_element(
                By.CSS_SELECTOR, "time[datetime]"
            ).get_attribute("datetime")

            # Current collection time
            collection_time = datetime.now().isoformat()

            return Tweet(
                username=username,
                text=tweet_element.find_element(
                    By.CSS_SELECTOR, '[data-testid="tweetText"]'
                ).text,
                tweet_url=tweet_url,
                timestamp=timestamp,
                collection_time=collection_time,
                engagement=self.extract_metrics(tweet_element),
            )

        except Exception as e:
            logging.error(f"Error processing tweet: {e}")
            return None

    def extract_tweet_url(self, tweet_element):
        try:
            tweet_url = tweet_element.find_element(
                By.CSS_SELECTOR, '[data-testid="User-Name"] div > a'
            ).get_attribute("href")
            return f"https://twitter.com{tweet_url}"
        except Exception as e:
            logging.error(f"Error extracting tweet URL: {e}")
            return None

    def extract_metrics(self, tweet_element):
        try:
            return {
                "replies": tweet_element.find_element(
                    By.CSS_SELECTOR, '[data-testid="reply"]'
                ).text,
                "retweets": tweet_element.find_element(
                    By.CSS_SELECTOR, '[data-testid="retweet"]'
                ).text,
                "likes": tweet_element.find_element(
                    By.CSS_SELECTOR, '[data-testid="like"]'
                ).text,
            }
        except Exception as e:
            logging.error(f"Error extracting metrics: {e}")
            return {}

    def search_and_extract(self, driver, keyword, target_tweets=100, timeout=300):
        tweets = []
        start_time = time.time()
        processed_urls = set()
        no_new_content_count = 0
        last_height = 0

        try:
            encoded_query = urllib.parse.quote(keyword)
            search_url = (
                f"https://twitter.com/search?q={encoded_query}&src=typed_query&f=live"
            )

            logging.info(f"Searching URL: {search_url}")
            driver.get(search_url)
            time.sleep(3)

            while len(tweets) < target_tweets and (time.time() - start_time) < timeout:
                # Get current scroll height
                current_height = driver.execute_script(
                    "return document.body.scrollHeight"
                )

                # Check if we're getting new content
                if current_height == last_height:
                    no_new_content_count += 1
                    if no_new_content_count >= 3:  # No new content after 3 attempts
                        logging.info(f"No more content for keyword: {keyword}")
                        break
                else:
                    no_new_content_count = 0

                last_height = current_height

                # Process visible tweets
                tweet_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                    )
                )

                for tweet_element in tweet_elements:
                    try:
                        tweet_url = tweet_element.find_element(
                            By.CSS_SELECTOR, '[data-testid="User-Name"] div > a'
                        ).get_attribute("href")

                        if tweet_url not in processed_urls:
                            tweet_data = self.extract_tweet_data(tweet_element)
                            if tweet_data:
                                tweets.append(tweet_data)
                                processed_urls.add(tweet_url)

                    except Exception as e:
                        logging.error(f"Error processing tweet: {e}")
                        continue

                # Scroll
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            return tweets

        except Exception as e:
            logging.error(f"Error in search_and_extract: {e}")
            return tweets
