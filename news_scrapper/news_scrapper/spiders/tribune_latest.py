# tribune_latest.py
import redis
from scrapy import Spider, Request
from datetime import datetime
import re
import logging
from scrapy.utils.log import configure_logging
import json
from collections import defaultdict
import os
from news_scrapper.items import NewsArticleItem
from news_scrapper.spiders.base_spider import NewsSpiderBase, SpiderConfig

class TribuneLatestSpider(NewsSpiderBase):

    name = 'tribune_latest'
    
    def __init__(self, *args, **kwargs):
        
        super(TribuneLatestSpider, self).__init__(*args, **kwargs)
        config = SpiderConfig(
            name='tribune_latest',
            allowed_domains=['tribune.com.pk'],
            start_urls=['https://tribune.com.pk/latest']
        )
        self.initialize(config)


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
            
            self.mark_article_scraped(response.url)

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

    