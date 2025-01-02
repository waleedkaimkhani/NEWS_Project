# tribune_latest.py
import sqlite3
from scrapy import Spider, Request
from datetime import datetime
import re
import logging
from scrapy.utils.log import configure_logging
import json
from collections import defaultdict
import os
from news_scrapper.items import NewsArticleItem

class TribuneLatestSpider(Spider):
    name = 'tribune_latest'
    allowed_domains = ['tribune.com.pk']
    start_urls = ['https://tribune.com.pk/latest']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'tribune_latest.log',
        'FEED_FORMAT': 'json',
        'FEED_URI': 'data/tribune_articles_%(time)s.json'
    }

    def __init__(self, *args, **kwargs):
        super(TribuneLatestSpider, self).__init__(*args, **kwargs)
        self.db_path = 'scraped_articles.db'
        self.init_db()
        self.today = datetime.now().date()
        self.stats = defaultdict(int)
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(self.name)
        return self._logger

    def setup_logging(self):

        os.makedirs('logs', exist_ok=True)
        configure_logging()
        logger = logging.getLogger(self.name)
        
        log_file = f'logs/tribune_scraper_{self.today}.log'
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        
        logger.handlers = []
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS tribune_articles
            (url TEXT,
             title TEXT,
             date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
             publish_date TEXT,
             category TEXT)
        ''')
        conn.commit()
        conn.close()

    def is_article_scraped(self, url):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT url FROM tribune_articles 
            WHERE url = ? AND date(date_scraped) = date('now')
        ''', (url,))
        result = c.fetchone()
        conn.close()
        return result is not None

    def parse(self, response):
        
        self.logger.info("Starting daily Tribune latest news scrape")
        
        # Tribune's latest news structure
        articles = response.xpath('/html/body/div[1]/div[4]/section/div/div/div[1]/div/div/div/ul[1]//li')
        
        articles_found = len(articles)
        self.logger.info(f"Found {articles_found} articles on Tribune latest news page")
        
        for article in articles:
            link = article.xpath('.//div/div[1]/div/a/@href').get()
            if link:
                # Ensure full URL
                
                if not link.startswith('http'):
                    link = f'https://tribune.com.pk{link}'
                
                if not self.is_article_scraped(link):
                    print(link)
                    yield Request(url=link, callback=self.parse_article)
                    self.stats['articles_found'] += 1

    def parse_article(self, response):
        try:
            # Extract article details based on Tribune's HTML structure
            heading = response.xpath('//*[@id="main-section"]/section/div[1]/div/div[1]/div/h1/text()').get()
            content = ' '.join(response.xpath('//*[@id="main-section"]/section/div[1]/div/div[1]/div/div/div/div/span[2]/p/text()').getall())
            author = response.xpath('//*[@id="main-section"]/section/div[1]/div/div[1]/div/span/div[1]/span[1]/a/text()').get()
            date_str = response.xpath('//*[@id="main-section"]/section/div[1]/div/div[1]/div/span/div[1]/span[2]/text()').get()
            category = response.xpath('/html/body/div[1]/div[3]/div/div/ul/li[2]/text()').get()
            
            # Clean data
            
            heading = heading.strip() if heading else None
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
                INSERT INTO tribune_articles (url, title, publish_date, category)
                VALUES (?, ?, ?, ?)
            ''', (response.url, heading, publish_date, category))
            conn.commit()
            conn.close()

            self.stats['articles_scraped'] += 1
            self.logger.info(f"Scraped Tribune article: {response.url}")

            yield NewsArticleItem(
                    heading=heading,
                    content=content,
                    author=author,
                    date=date_str,
                    category=category,
                    url=response.url
                )

        except Exception as e:
            self.logger.error(f"Error parsing Tribune article {response.url}: {str(e)}")
            self.stats['errors'] += 1

    def closed(self, reason):
        os.makedirs('stats', exist_ok=True)
        
        stats_report = {
            'date': self.today.isoformat(),
            'articles_found': self.stats['articles_found'],
            'articles_scraped': self.stats['articles_scraped'],
            'errors': self.stats['errors'],
            'reason': reason
        }
        
        stats_file = f'stats/tribune_stats_{self.today}.json'
        with open(stats_file, 'w') as f:
            json.dump(stats_report, f, indent=4)
        
        self.logger.info(f"Tribune scraping completed. Total articles scraped: {self.stats['articles_scraped']}")