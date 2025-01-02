from prefect import flow, task
import psycopg2
from prefect.logging import get_run_logger
from psycopg2.extras import execute_values
import json
import os
from datetime import datetime
from typing import List, Dict
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from news_scrapper.spiders.Dawn_spider import DawnLatestSpider
from news_scrapper.spiders.tribune_latest import TribuneLatestSpider

# Database configuration
DB_CONFIG = {
    "dbname": "news_db",
    "user": "admin",
    "password": "admin123",
    "host": "localhost",
    "port": "5432"
}

@task(retries=3, retry_delay_seconds=30, name="setup_database")
def setup_database() -> None:
    """Create database table with proper constraints for handling duplicates"""
    logger = get_run_logger()
    logger.info("Setting up database...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            heading TEXT NOT NULL,
            content TEXT,
            author TEXT,
            date DATE,
            category TEXT,
            url TEXT UNIQUE,  -- Making URL unique to prevent duplicates
            processed_at TIMESTAMP,
            spider_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create index on URL for faster duplicate checking
        CREATE INDEX IF NOT EXISTS idx_news_url ON news(url);
        """
        cur.execute(create_table_query)
        conn.commit()
        logger.info("Database setup completed successfully")
    finally:
        cur.close()
        conn.close()

@task(retries=2, retry_delay_seconds=60, name="run_scrapers")
def run_scrapers() -> None:
    """Task to run the scrapers in parallel"""
    logger = get_run_logger()
    logger.info("Starting scrapers...")
    
    process = CrawlerProcess(get_project_settings())
    process.crawl(DawnLatestSpider)
    process.crawl(TribuneLatestSpider)
    process.start()
    
    logger.info("Scrapers completed successfully")

@task(name="load_json_files")
def load_json_files(json_dir: str) -> List[Dict]:
    """Load and combine all JSON files from the specified directory"""
    logger = get_run_logger()
    logger.info(f"Loading JSON files from {json_dir}")
    
    all_articles = []
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(json_dir, filename)
            with open(file_path, "r") as file:
                articles = json.load(file)
                all_articles.extend(articles)
    
    logger.info(f"Loaded {len(all_articles)} articles")
    return all_articles

@task(retries=3, retry_delay_seconds=30, name="upsert_articles")
def upsert_articles(articles: List[Dict]) -> int:
    """Insert or update articles in the database"""
    logger = get_run_logger()
    logger.info(f"Upserting {len(articles)} articles")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        upsert_query = """
        INSERT INTO news (
            heading, content, author, date, category, url, processed_at, spider_name
        ) VALUES %s
        ON CONFLICT (url) DO UPDATE SET
            heading = EXCLUDED.heading,
            content = EXCLUDED.content,
            author = EXCLUDED.author,
            date = EXCLUDED.date,
            category = EXCLUDED.category,
            processed_at = EXCLUDED.processed_at,
            spider_name = EXCLUDED.spider_name,
            updated_at = CURRENT_TIMESTAMP
        """
        
        article_data = [
            (
                article.get("heading"),
                article.get("content"),
                article.get("author"),
                article.get("date"),
                article.get("category"),
                article.get("url"),
                article.get("processed_at"),
                article.get("spider_name")
            )
            for article in articles
        ]
        
        execute_values(cur, upsert_query, article_data)
        conn.commit()
        logger.info(f"Successfully upserted {len(articles)} articles")
        return len(articles)
        
    finally:
        cur.close()
        conn.close()

@task(name="cleanup_json_files")
def cleanup_json_files(json_dir: str) -> None:
    """Clean up processed JSON files"""
    logger = get_run_logger()
    logger.info("Cleaning up JSON files")
    
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(json_dir, filename)
            os.remove(file_path)
    
    logger.info("Cleanup completed")

@flow(name="news_etl_pipeline", log_prints=True)
def news_etl_pipeline(json_dir: str = "./data/articles"):
    """Main ETL pipeline flow"""
    logger = get_run_logger()
    logger.info("Starting news ETL pipeline")
    
    try:
        # Initialize database
        setup_database()
        
        # Run scrapers
        run_scrapers()
        
        # Load JSON files
        articles = load_json_files(json_dir)
        
        if articles:
            # Store data in PostgreSQL
            articles_processed = upsert_articles(articles)
            
            # Cleanup JSON files after successful processing
            cleanup_json_files(json_dir)
            
            logger.info(f"Pipeline completed successfully! Processed {articles_processed} articles")
            return articles_processed
        else:
            logger.info("No articles found to process")
            return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    news_etl_pipeline()