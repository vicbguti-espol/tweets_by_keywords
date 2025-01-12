# Twitter Scraper

A tool for scraping tweets based on keywords with authentication support.

## Quick Start

1. Configure your credentials in `config/credentials.json`:
```json
{
    "username": "your-twitter-username",
    "password": "your-twitter-password"
}
```

2. Set up your search parameters in `config/config.json`:
```json
{
    "keyword_file": "config/keywords.txt",
    "browser_settings": {
        "headless": false,
        "tweets_per_keyword": 100
    },
    "cookie_file": "twitter_cookies.pkl"
}
```

3. Create your `config/keywords.txt` with search terms:
```plaintext
seguridad guayaquil
violencia guayaquil guayas
```

4. Run the scraper:
```bash
python run.py
```

## Output

Tweets will be saved in JSON format under `data/output/` with timestamps like `tweets_20250112_131447.json`:
```json
{
    "username": "@example",
    "text": "Tweet content",
    "tweet_url": "https://twitter.com/...",
    "timestamp": "2025-01-12T18:13:19.000Z",
    "collection_time": "2025-01-12T13:13:59.009484",
    "engagement": {
        "replies": "",
        "retweets": "",
        "likes": ""
    },
    "keyword": "search keyword"
}
```

## Requirements

- Python 3.7+
- Chrome browser
