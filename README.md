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
    "keywords": ["keyword1", "keyword2"],
    "browser_settings": {
        "headless": false,
        "tweets_per_keyword": 100
    },
    "cookie_file": "twitter_cookies.pkl"
}
```

3. Run the scraper:
```bash
python run.py
```

## Output

Tweets will be saved in JSON format under `data/output/` with timestamps.

## Requirements

- Python 3.7+
- Chrome browser
