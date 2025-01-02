from news_pipeline import news_etl_pipeline
from datetime import timedelta

if __name__ == "__main__":
    news_etl_pipeline.serve(
        name="news_scraper",
        interval=timedelta(hours=24),
        tags=["news", "scraping"],
        description="Scrapes news articles from Dawn and Tribune websites"
    )