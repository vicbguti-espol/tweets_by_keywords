from src.models.tweet import Tweet
import json
import logging
from typing import List, Dict
import os


class TweetSaver:
    def save_to_json(self, tweets: List[Tweet], filename: str) -> bool:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            tweet_data = [tweet.__dict__ for tweet in tweets]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(tweet_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(tweets)} tweets to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error saving JSON: {e}")
            return False
