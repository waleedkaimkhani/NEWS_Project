# simple_parallel.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from news_scrapper.spiders.Dawn_spider import DawnLatestSpider
from news_scrapper.spiders.tribune_latest import TribuneLatestSpider

def setup_logging():
    """Configure logging"""
    os.makedirs('logs', exist_ok=True)
    log_file = f'logs/scraper_{datetime.now().date()}.log'
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('news_scraper')

def run_spiders():
    logger = setup_logging()
    logger.info("Starting news scraping")
    
    try:
        # Initialize the process
        process = CrawlerProcess(get_project_settings())
        
        # Add both spiders to the process
        process.crawl(DawnLatestSpider)
        process.crawl(TribuneLatestSpider)
        
        # Start the crawling process
        process.start()
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    run_spiders()