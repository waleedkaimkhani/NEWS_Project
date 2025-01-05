# base_spider.py
import redis
from scrapy import Spider, Request
from datetime import datetime
import logging
from scrapy.utils.log import configure_logging
import json
from collections import defaultdict
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class SpiderConfig:
    """Configuration class for spider settings"""
    name: str
    allowed_domains: List[str]
    start_urls: List[str]
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    url_expiry: int = 86400
    concurrent_requests: int = 16
    download_delay: float = 2.0
    
    @property
    def custom_settings(self) -> Dict[str, Any]:
        return {
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': self.concurrent_requests,
            'DOWNLOAD_DELAY': self.download_delay,
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': f'logs/{self.name}.log',
            'FEED_FORMAT': 'json',
            'FEED_URI': f'data/{self.name}_articles_%(time)s.json'
        }

class NewsSpiderBase(Spider, ABC):
    """Base spider class with common functionality"""
    
    def __init__(self,*args, **kwargs):
        
        super(NewsSpiderBase, self).__init__(*args, **kwargs)

        
    def initialize(self, config: SpiderConfig) -> None:
        """Initialize spider with configuration"""

        self.config = config
       
        self.allowed_domains = config.allowed_domains
        self.start_urls = config.start_urls
        self.custom_settings = config.custom_settings
        
        # Initialize Redis
        
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
        self.today = datetime.now().date()
        self.stats = defaultdict(int)
        self._logger = None
        self.setup_logging()
        

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(self.name)
        return self._logger

    def setup_logging(self):
        """Set up logging configuration"""
        os.makedirs('logs', exist_ok=True)
        configure_logging()
        
        logger = logging.getLogger(self.name)
        log_file = f'logs/{self.name}_{self.today}.log'
        
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        
        logger.handlers = []
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)

    def is_article_scraped(self, url: str) -> bool:
        """Check if article URL exists in Redis"""
        if not self.redis_client:
            return False
        return bool(self.redis_client.get(f"{self.name}:url:{url}"))

    def mark_article_scraped(self, url: str) -> None:
        """Mark URL as scraped in Redis with expiration"""
        if self.redis_client:
            self.redis_client.setex(
                f"{self.name}:url:{url}",
                self.config.url_expiry,
                "1"
            )

    @abstractmethod
    def parse_article(self, response) -> Dict[str, Any]:
        """Parse individual article page"""
        pass

    def closed(self, reason: str) -> None:
        """Handle spider closure and save statistics"""
        os.makedirs('stats', exist_ok=True)
        
        stats_report = {
            'date': self.today.isoformat(),
            'articles_found': self.stats['articles_found'],
            'articles_scraped': self.stats['articles_scraped'],
            'errors': self.stats['errors'],
            'reason': reason
        }
        
        stats_file = f'stats/{self.name}_stats_{self.today}.json'
        with open(stats_file, 'w') as f:
            json.dump(stats_report, f, indent=4)
        
        self.logger.info(
            f"Scraping completed. Total articles scraped: {self.stats['articles_scraped']}"
        )

    def handle_article_error(self, url: str, error: Exception) -> None:
        """Handle and log article parsing errors"""
        self.logger.error(f"Error parsing article {url}: {str(error)}")
        self.stats['errors'] += 1