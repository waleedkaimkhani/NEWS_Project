# config.py
SCRAPER_CONFIG = {
    'process_count': 2,  # Number of parallel processes
    'timeout': 300,      # Timeout in seconds
    'database': {
        'path': 'scraped_articles.db',
        'timeout': 30
    },
    'dawn': {
        'concurrent_requests': 8,
        'download_delay': 1,
        'batch_size': 50
    },
    'tribune': {
        'concurrent_requests': 8,
        'download_delay': 1,
        'batch_size': 50
    },
    'export': {
        'format': 'json',
        'compression': 'gz'
    }
}

# Retry configuration
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 10,
    'retry_statuses': [500, 502, 503, 504, 408]
}

# Rate limiting
RATE_LIMITS = {
    'dawn.com': '10/m',      # 10 requests per minute
    'tribune.com.pk': '10/m'  # 10 requests per minute
}