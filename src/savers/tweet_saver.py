from src.models.tweet import Tweet
import json
import csv
from datetime import datetime
import logging
from typing import List, Dict


class TweetSaver:
    def save_to_json(self, tweets: List[Tweet], filename: str) -> bool:
        try:
            tweet_data = [tweet.__dict__ for tweet in tweets]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(tweet_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(tweets)} tweets to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error saving JSON: {e}")
            return False

    def save_to_csv(self, tweets: List[Tweet], keyword: str, filename: str) -> bool:
        fieldnames = [
            "keyword",
            "username",
            "tweet_url",
            "reply_to",
            "tweet_text",
            "timestamp",
            "replies",
            "retweets",
            "likes",
        ]
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for tweet in tweets:
                    writer.writerow(
                        {
                            "keyword": keyword,
                            "username": tweet.username,
                            "tweet_url": tweet.tweet_url,
                            "reply_to": tweet.reply_to,
                            "tweet_text": tweet.text,
                            "timestamp": tweet.timestamp,
                            "replies": tweet.engagement["replies"],
                            "retweets": tweet.engagement["retweets"],
                            "likes": tweet.engagement["likes"],
                        }
                    )
            return True
        except Exception as e:
            logging.error(f"Error saving CSV: {e}")
            return False
