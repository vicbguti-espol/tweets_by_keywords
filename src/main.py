from src.extractors.tweet_extractor import TweetExtractor
from src.savers.tweet_saver import TweetSaver
from src.utils.browser import Browser
import logging
from datetime import datetime
import os


def main():
    browser = None
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Initialize components
        browser = Browser()
        extractor = TweetExtractor()
        saver = TweetSaver()

        # Get keywords from file
        keywords = extractor.parse_keywords("config/keywords.txt")
        all_tweets = []

        # Extract tweets for each keyword
        for keyword in keywords:
            tweets = extractor.search_and_extract(browser.driver, keyword)
            if tweets:
                all_tweets.extend(tweets)

        # Save tweets with timestamp
        if all_tweets:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join("data", "output", f"tweets_{timestamp}.json")
            saver.save_to_json(all_tweets, output_file)

        # Save search results status
        extractor.save_search_results()

    except Exception as e:
        logging.error(f"Error in main: {e}")
        raise
    finally:
        if browser:
            browser.close()


if __name__ == "__main__":
    main()
