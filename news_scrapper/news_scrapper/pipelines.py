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