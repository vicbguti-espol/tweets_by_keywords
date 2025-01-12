from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Tweet:
    username: str
    text: str
    tweet_url: str
    timestamp: str  # Tweet's original timestamp
    collection_time: str  # When we collected it
    engagement: Dict[str, str] = None

    def __post_init__(self):
        if not self.engagement:
            self.engagement = {"replies": "0", "retweets": "0", "likes": "0"}
