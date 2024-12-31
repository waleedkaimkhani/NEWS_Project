# spider_base.py
from scrapy import Spider
import sqlite3
import logging
from datetime import datetime
import os
from multiprocessing import Lock

class NewsSpiderBase(Spider):
    # Shared database lock
    db_lock = Lock()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.today = datetime.now().date()
        self.setup_logging()
        
    def setup_logging(self):
        """Set up spider-specific logging"""
        log_dir = f'logs/{self.name}'
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = f'{log_dir}/{self.today}.log'
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        self.logger = logging.getLogger(self.name)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def get_db_connection(self):
        """Get database connection with lock"""
        with self.db_lock:
            return sqlite3.connect(self.db_path)

    def execute_db_query(self, query, params=None):
        """Execute database query with lock"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            try:
                c = conn.cursor()
                if params:
                    c.execute(query, params)
                else:
                    c.execute(query)
                conn.commit()
                result = c.fetchall()
                return result
            finally:
                conn.close()