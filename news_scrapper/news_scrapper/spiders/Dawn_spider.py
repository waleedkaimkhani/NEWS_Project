# dawn_latest.py
import redis
from scrapy import Spider, Request
from datetime import datetime, timedelta
import re
import logging
from scrapy.utils.log import configure_logging
import json
from collections import defaultdict
import os
from news_scrapper.items import NewsArticleItem
from news_scrapper.spiders.base_spider import NewsSpiderBase, SpiderConfig

class DawnLatestSpider(NewsSpiderBase):
    name = 'dawn_latest'
    
    def __init__(self, *args, **kwargs):
        super(DawnLatestSpider, self).__init__(*args, **kwargs)
        
        super(DawnLatestSpider, self).__init__(*args, **kwargs)
        config = SpiderConfig(
            name='dawn_latest',
            allowed_domains=['dawn.com'],
            start_urls=['https://www.dawn.com/latest-news']
        )
        self.initialize(config)
       
    def parse(self, response):

        self.logger.info("Starting daily latest news scrape")
        articles = response.xpath('/html/body/div[2]/div/div/div[1]/div/div/div/div[1]/article')
       
        articles_found = len(articles)
        self.logger.info(f"Found {articles_found} articles on latest news page")
        
        # Only process the first page of latest news
        for article in articles:
           
            link = article.xpath('.//div/div[1]/figure/div/a/@href').get()
            
            if link and not self.is_article_scraped(link):
                yield Request(url=link, callback=self.parse_article)
                self.stats['articles_found'] += 1

    def parse_article(self, response):
        
        try:
            # Extract article details
          
            heading = response.xpath('/html/body/div[2]/div[1]/div/article/div[2]/h2/a/text()').get()
            
            content = ' '.join(response.xpath('/html/body/div[2]/div[1]/div/article/div[3]/div[2]/p/text()').getall())
            
            author = '|'.join(response.xpath('/html/body/div[2]/div[1]/div/article/div[2]/div[1]/span[1]/a/text()').getall())
            
            date_str = response.xpath('/html/body/div[2]/div[1]/div/article/div[2]/div[1]/span[3]/span[1]/span[2]/text()').get()
            
            category = response.xpath('/html/body/div[2]/div[1]/div/article/div[4]/div[1]/div[3]/div[1]/div/div/div/span/a/@title').get()
          
    
            # Clean and process the data
            heading = heading.strip() if heading else None
            content = content.strip() if content else None
            author = author.strip() if author else None
            category = category.strip() if category else None
            
           
            publish_date = None
            if date_str:
                try:
                    publish_date = datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    self.logger.warning(f"Could not parse date: {date_str}")

            # Store in database
            self.mark_article_scraped(response.url)
            
            self.stats['articles_scraped'] += 1
            self.logger.info(f"Scraped article: {heading}")

            yield NewsArticleItem(
                        heading=heading,
                        content=content,
                        author=author,
                        date=date_str,
                        category=category,
                        url=response.url
            )

        except Exception as e:
            self.logger.error(f"Error parsing article {response.url}: {str(e)}")
            self.stats['errors'] += 1

    