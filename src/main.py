from src.extractors.tweet_extractor import TweetExtractor
from src.savers.tweet_saver import TweetSaver
from src.utils.browser import Browser
from src.models.tweet import Tweet
import logging
import time
import json
from datetime import datetime
import os


def main():
    # Initialize components
    browser = Browser()
    extractor = TweetExtractor()
    saver = TweetSaver()

    # Setup logging
    browser.setup_logging()

    all_tweets = []

    try:
        # Load configuration
        with open("config/config.json") as f:
            config = json.load(f)

        # Load cookies
        cookie_path = os.path.join("data", "cookies", config["cookie_file"])
        if not browser.load_cookies(cookie_path):
            logging.error("Failed to load cookies")
            return

        # Load and parse keywords
        keywords = extractor.parse_keywords(config["keyword_file"])
        if not keywords:
            logging.error("No keywords found")
            return

        # Search keywords
        for keyword in keywords:
            logging.info(f"Searching for: {keyword}")
            tweets = extractor.search_and_extract(
                browser.driver,
                keyword,
                target_tweets=config["browser_settings"]["tweets_per_keyword"],
            )

            if tweets:
                for tweet in tweets:
                    tweet.keyword = keyword
                all_tweets.extend(tweets)

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join("data", "output", f"tweets_{timestamp}.json")

        # Save all tweets
        if all_tweets:
            if saver.save_to_json(all_tweets, output_file):
                logging.info(f"Saved {len(all_tweets)} tweets to {output_file}")

    except Exception as e:
        logging.error(f"Error in main: {e}")
    finally:
        browser.close()


if __name__ == "__main__":
    main()
