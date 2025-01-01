import sqlite3
from datetime import datetime
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
import logging
import os
import json

class NewsValidationPipeline:
    """Validates and cleans article data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Check required fields
        required_fields = ['heading', 'url']
        for field in required_fields:
            if not adapter.get(field):
                raise DropItem(f"Missing {field} in {adapter.get('url')}")
        
        # Clean text fields
        text_fields = ['heading', 'content', 'author', 'category']
        for field in text_fields:
            if adapter.get(field):
                adapter[field] = adapter[field].strip()
        
        # Add metadata
        adapter['processed_at'] = datetime.now().isoformat()
        adapter['spider_name'] = spider.name
        
        return item

class DuplicateCheckPipeline:
    """Checks for duplicate articles"""
    
    def __init__(self):
        self.urls_seen = set()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter['url']
        
        if url in self.urls_seen:
            raise DropItem(f"Duplicate article found: {url}")
        
        self.urls_seen.add(url)
        return item

class SQLitePipeline:
    """Stores articles in SQLite database"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_path=crawler.settings.get('SQLITE_DB_PATH', 'news_articles.db')
        )
    
    def open_spider(self, spider):
        self.conn = sqlite3.connect(self.db_path)
        self.curr = self.conn.cursor()
        # Create tables if they don't exist
        self.curr.execute('''
            CREATE TABLE IF NOT EXISTS articles
            (url TEXT PRIMARY KEY,
             title TEXT NOT NULL,
             content TEXT,
             author TEXT,
             publish_date TIMESTAMP,
             category TEXT,
             source TEXT,
             spider_name TEXT,
             processed_at TIMESTAMP,
             date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        ''')
        self.conn.commit()
    
    def close_spider(self, spider):
        self.conn.close()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        try:
            self.curr.execute('''
                INSERT OR REPLACE INTO articles
                (url, title, content, author, publish_date, category, source, 
                 spider_name, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter['url'],
                adapter['heading'],
                adapter.get('content'),
                adapter.get('author'),
                adapter.get('date'),
                adapter.get('category'),
                adapter.get('source'),
                adapter.get('spider_name'),
                adapter.get('processed_at')
            ))
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Error storing article {adapter['url']}: {str(e)}")
            raise
            
        return item

class JsonExportPipeline:
    """Exports articles to JSON files organized by date and source"""
    
    def __init__(self):
        self.items = []
        self.export_dir = 'data/articles'
        os.makedirs(self.export_dir, exist_ok=True)
    
    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item
    
    def close_spider(self, spider):
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{self.export_dir}/{spider.name}_{date_str}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.items, f, indent=4)