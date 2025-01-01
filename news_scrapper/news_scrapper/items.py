# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from scrapy import Item, Field

class NewsArticleItem(Item):
    """Define structured data model for news articles"""
    heading = Field()
    content = Field()
    author = Field()
    date = Field()
    category = Field()
    url = Field()
    source = Field()  # To identify which news site
    spider_name = Field()
    scrape_date = Field()
