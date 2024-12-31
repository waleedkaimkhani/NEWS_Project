# run_daily_scrape.py
import os
import sys
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.Dawn_spider import DawnLatestSpider
from spiders.tribune_latest import TribuneLatestSpider
import logging

def setup_directories():
    """Create necessary directories if they don't exist"""
    dirs = ['logs', 'data', 'stats']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def setup_logging():
    """Set up logging for the main script"""
    logging.basicConfig(
        filename=f'logs/scraper_main_{datetime.now().date()}.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('main_scraper')

def run_spiders():
    """Run both Dawn and Tribune spiders"""
    logger = setup_logging()
    setup_directories()
    
    try:
        # Initialize crawler process
        settings = get_project_settings()
        process = CrawlerProcess(settings)
        
        # Add both spiders to the process
        logger.info("Starting Dawn spider")
        process.crawl(DawnLatestSpider)
        
        logger.info("Starting Tribune spider")
        process.crawl(TribuneLatestSpider)
        
        # Start the crawling process
        logger.info("Beginning crawling process")
        process.start()
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    run_spiders()