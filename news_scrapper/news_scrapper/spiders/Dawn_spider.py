# dawn_latest.py
import sqlite3
from scrapy import Spider, Request
from datetime import datetime, timedelta
import re
import logging
from scrapy.utils.log import configure_logging
import json
from collections import defaultdict
import os
from news_scrapper.items import NewsArticleItem

class DawnLatestSpider(Spider):
    name = 'dawn_latest'
    allowed_domains = ['dawn.com']
    start_urls = ['https://www.dawn.com/latest-news']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'dawn_latest.log',
        # Export settings
        'FEED_FORMAT': 'json',
        'FEED_URI': 'data/dawn_articles_%(time)s.json'
    }

    def __init__(self, *args, **kwargs):
        super(DawnLatestSpider, self).__init__(*args, **kwargs)
        self.db_path = 'scraped_articles.db'
        self.init_db()
        self.today = datetime.now().date()
        
        # Initialize statistics
        self.stats = defaultdict(int)
        
        # Set up logging
        self.setup_logging()
        # Create a class attribute for logger
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(self.name)
        return self._logger

    def setup_logging(self):
        """Set up logging configuration"""
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        configure_logging()
        logger = logging.getLogger(self.name)
        
        # Create file handler with date in filename
        log_file = f'logs/dawn_scraper_{self.today}.log'
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers = []
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)

    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS articles
            (url TEXT PRIMARY KEY,
             title TEXT,
             date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
             publish_date DATE,
             category TEXT)
        ''')
        conn.commit()
        conn.close()

    def is_article_scraped(self, url):
        """Check if article URL has been scraped today"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT url FROM articles 
            WHERE url = ? AND date(date_scraped) = date('now')
        ''', (url,))
        result = c.fetchone()
        conn.close()
        return result is not None

    def parse(self, response):
        self.logger.info("Starting daily latest news scrape")
        articles = response.css('article.story')
        articles_found = len(articles)
        self.logger.info(f"Found {articles_found} articles on latest news page")
        
        # Only process the first page of latest news
        for article in articles:
            link = article.css('h2 a::attr(href)').get()
            if link and not self.is_article_scraped(link):
                yield Request(url=link, callback=self.parse_article)
                self.stats['articles_found'] += 1

    def parse_article(self, response):
        try:
            # Extract article details
            title = response.css('h1.story__title::text').get()
            content = ' '.join(response.css('div.story__content p::text').getall())
            author = response.css('span.story__byline a::text').get()
            date_str = response.css('span.story__time::attr(datetime)').get()
            category = response.css('span.story__category a::text').get()
            
            # Clean and process the data
            title = title.strip() if title else None
            content = content.strip() if content else None
            author = author.strip() if author else None
            category = category.strip() if category else None
            
            # Parse date
            publish_date = None
            if date_str:
                try:
                    publish_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    self.logger.warning(f"Could not parse date: {date_str}")

            # Store in database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO articles (url, title, publish_date, category)
                VALUES (?, ?, ?, ?)
            ''', (response.url, title, publish_date, category))
            conn.commit()
            conn.close()

            self.stats['articles_scraped'] += 1
            self.logger.info(f"Scraped article: {title}")

            yield NewsArticleItem(
                        title=title,
                        content=content,
                        author=author,
                        date=date_str,
                        category=category,
                        url=response.url
            )

        except Exception as e:
            self.logger.error(f"Error parsing article {response.url}: {str(e)}")
            self.stats['errors'] += 1

    def closed(self, reason):
        """Log final statistics when spider closes"""
        # Ensure stats directory exists
        os.makedirs('stats', exist_ok=True)
        
        stats_report = {
            'date': self.today.isoformat(),
            'articles_found': self.stats['articles_found'],
            'articles_scraped': self.stats['articles_scraped'],
            'errors': self.stats['errors'],
            'reason': reason
        }
        
        # Save daily statistics
        stats_file = f'stats/dawn_stats_{self.today}.json'
        with open(stats_file, 'w') as f:
            json.dump(stats_report, f, indent=4)
        
        self.logger.info(f"Scraping completed. Total articles scraped: {self.stats['articles_scraped']}")