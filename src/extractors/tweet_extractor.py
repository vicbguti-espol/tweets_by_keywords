from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.models.tweet import Tweet  # Updated import path
import logging
import time
import urllib.parse
from datetime import datetime
import os
import json
from typing import Set, List, Dict


class TweetExtractor:
    def __init__(self):
        self.processed_tweet_urls: Set[str] = set()
        self.processed_comment_urls: Set[str] = set()
        self.search_results = {"successful": [], "failed": []}
        self.load_existing_tweets()

    def load_existing_tweets(self):
        output_dir = os.path.join("data", "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            return

        for file in os.listdir(output_dir):
            if file.endswith(".json"):
                try:
                    with open(
                        os.path.join(output_dir, file), "r", encoding="utf-8"
                    ) as f:
                        tweets = json.load(f)
                        for tweet in tweets:
                            self.processed_tweet_urls.add(tweet["tweet_url"])
                except Exception as e:
                    logging.error(f"Error loading existing tweets from {file}: {e}")

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
            tweet_url = f"{tweet_link.get_attribute('href')}"

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
            # Look for the timestamp link which leads to the actual tweet
            time_element = tweet_element.find_element(By.CSS_SELECTOR, "time[datetime]")
            tweet_url = time_element.find_element(
                By.XPATH, ".."  # Parent element of time
            ).get_attribute("href")

            return tweet_url
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

    def extract_comments(
        self, driver, tweet_url: str, min_replies: int = 0
    ) -> List[Dict]:
        comments = []
        try:
            driver.get(tweet_url)
            time.sleep(5)  # Increased wait for page load

            # Verify we're on the tweet detail page
            if not tweet_url in driver.current_url:
                logging.warning(f"Failed to load tweet page: {tweet_url}")
                return comments

            # Check for replies section
            try:
                reply_section = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (
                            By.CSS_SELECTOR,
                            'div[data-testid="cellInnerDiv"]:not(:first-child) article[data-testid="tweet"]',
                        )
                    )
                )

                if not reply_section:
                    logging.debug(f"No reply section found for tweet: {tweet_url}")
                    return comments

                last_height = driver.execute_script("return document.body.scrollHeight")
                scroll_attempts = 0
                max_scrolls = 5  # Increased max scrolls

                while scroll_attempts < max_scrolls:
                    # Process visible replies
                    reply_tweets = driver.find_elements(
                        By.CSS_SELECTOR,
                        'div[data-testid="cellInnerDiv"]:not(:first-child) article[data-testid="tweet"]',
                    )

                    for reply in reply_tweets:
                        try:
                            comment_url = self.extract_tweet_url(reply)
                            if (
                                comment_url
                                and comment_url not in self.processed_comment_urls
                            ):
                                comment_data = self.extract_tweet_data(reply)
                                if comment_data:
                                    comment_data.parent_tweet_url = tweet_url
                                    comments.append(comment_data)
                                    self.processed_comment_urls.add(comment_url)
                                    logging.info(
                                        f"Extracted comment {comment_url} for tweet {tweet_url}"
                                    )
                        except Exception as e:
                            logging.error(f"Error processing comment: {e}")
                            continue

                    # Scroll down
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(3)  # Increased scroll wait

                    new_height = driver.execute_script(
                        "return document.body.scrollHeight"
                    )
                    if new_height == last_height:
                        scroll_attempts += 1
                    else:
                        scroll_attempts = 0  # Reset counter if new content found
                    last_height = new_height

                logging.info(
                    f"Extracted {len(comments)} comments from tweet: {tweet_url}"
                )

            except Exception as e:
                logging.error(f"Error extracting comments: {e}")

        except Exception as e:
            logging.error(f"Error accessing tweet: {e}")
        finally:
            # Return to search results
            driver.back()
            time.sleep(3)

        return comments

    def search_and_extract(self, driver, keyword, target_tweets=100, timeout=300):
        tweets = []
        start_time = time.time()
        no_new_content_count = 0
        last_height = 0
        processed_urls_count = len(self.processed_tweet_urls)

        try:
            encoded_query = urllib.parse.quote(keyword)
            search_url = (
                f"https://twitter.com/search?q={encoded_query}&src=typed_query&f=live"
            )

            logging.info(f"Starting search for keyword: {keyword}")
            driver.get(search_url)
            time.sleep(5)  # Increased initial wait

            while len(tweets) < target_tweets and (time.time() - start_time) < timeout:
                tweet_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                    )
                )

                if not tweet_elements:
                    logging.info(f"No tweets found for keyword: {keyword}")
                    break

                for tweet_element in tweet_elements:
                    try:
                        tweet_url = self.extract_tweet_url(tweet_element)
                        if not tweet_url:
                            continue

                        if tweet_url not in self.processed_tweet_urls:
                            tweet_data = self.extract_tweet_data(tweet_element)
                            if tweet_data:
                                tweet_data.keyword = keyword  # Track source keyword
                                tweets.append(tweet_data)
                                self.processed_tweet_urls.add(tweet_url)

                                # Extract comments if tweet has replies
                                engagement = self.extract_metrics(tweet_element)
                                if (
                                    engagement.get("replies")
                                    and engagement["replies"] != "0"
                                ):
                                    comments = self.extract_comments(driver, tweet_url)
                                    if comments:
                                        for comment in comments:
                                            comment.parent_tweet_url = tweet_url
                                            comment.keyword = keyword
                                        tweets.extend(comments)

                                logging.info(f"Processed tweet: {tweet_url}")

                    except Exception as e:
                        logging.error(f"Error processing tweet: {e}")
                        continue

                # Scroll handling
                current_height = driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if current_height == last_height:
                    no_new_content_count += 1
                    if no_new_content_count >= 3:  # 3 attempts without new content
                        break
                else:
                    no_new_content_count = 0

                last_height = current_height
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increased scroll wait

            # Track search results
            new_urls_found = len(self.processed_tweet_urls) - processed_urls_count
            if new_urls_found > 0:
                self.search_results["successful"].append(
                    {"keyword": keyword, "tweets_found": new_urls_found}
                )
                logging.info(f"Found {new_urls_found} new tweets for '{keyword}'")
            else:
                self.search_results["failed"].append(
                    {"keyword": keyword, "reason": "No new tweets found"}
                )
                logging.warning(f"No new tweets found for '{keyword}'")

            return tweets

        except Exception as e:
            logging.error(f"Error searching for '{keyword}': {e}")
            self.search_results["failed"].append({"keyword": keyword, "reason": str(e)})
            return tweets

    def save_search_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(
            "data", "output", f"search_results_{timestamp}.json"
        )

        try:
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(self.search_results, f, ensure_ascii=False, indent=2)
            logging.info(f"Search results saved to {results_file}")
        except Exception as e:
            logging.error(f"Error saving search results: {e}")

    def parse_keywords(self, keyword_file: str) -> list:
        """Parse keywords from file with line breaks"""
        try:
            with open(keyword_file, "r", encoding="utf-8") as f:
                keywords = [line.strip() for line in f.readlines() if line.strip()]
            return keywords
        except Exception as e:
            logging.error(f"Error reading keywords file: {e}")
            return []
