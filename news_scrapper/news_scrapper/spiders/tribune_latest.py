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
import feedparser
from bs4 import BeautifulSoup
from ..items import NewsArticleItem
from .base_spider import NewsSpiderBase, SpiderConfig

class TribuneLatestSpider(NewsSpiderBase):

    name = 'tribune_latest'
    
    def __init__(self, *args, **kwargs):
        super(TribuneLatestSpider, self).__init__(*args, **kwargs)
        config = SpiderConfig(
            name='tribune_latest',
            allowed_domains=['tribune.com.pk'],
            start_urls=['https://tribune.com.pk/feed/latest']
        )
        self.initialize(config)

    def parse(self, response):
        self.logger.info("Starting daily Tribune latest news scrape from RSS feed")
        feed = feedparser.parse(response.body)
        
        articles_found_in_feed = len(feed.entries)
        self.logger.info(f"Found {articles_found_in_feed} articles in the feed")

        for entry in feed.entries:
            link = entry.get('link')
            if link:
                if not link.startswith('http'):
                    link = f'https://tribune.com.pk{link}'
                
                if not self.is_article_scraped(link):
                    yield Request(url=link, callback=self.parse_article, meta={'feed_entry': entry})
                    self.stats['articles_found'] += 1
            elif not link:
                self.logger.warning("Feed entry found without a link.")

    def parse_article(self, response):
        feed_entry = response.meta.get('feed_entry', {})
        item = NewsArticleItem()
        item['url'] = response.url

        try:
            item['heading'] = feed_entry.get('title')

            author_detail = feed_entry.get('author_detail')
            if author_detail and isinstance(author_detail, dict):
                item['author'] = author_detail.get('name')
            else:
                item['author'] = feed_entry.get('author')

            original_date_str = feed_entry.get('published')
            item['date'] = original_date_str
            date_str_for_parsing = original_date_str

            # Category extraction logic starts here
            category_val = None
            # feed_entry is already defined
            if feed_entry and feed_entry.get('tags') and isinstance(feed_entry.tags, list) and len(feed_entry.tags) > 0:
                tag_obj = feed_entry.tags[0]
                if isinstance(tag_obj, dict):
                    category_val = tag_obj.get('term')
                elif hasattr(tag_obj, 'term'):
                    category_val = tag_obj.term

                if category_val:
                    category_val = category_val.strip()
            item['category'] = category_val
            # End of category extraction logic

            # Content extraction logic starts here
            content_html = None
            content_text = None
            # feed_entry is already defined

            if feed_entry:
                if feed_entry.get('content') and isinstance(feed_entry.content, list) and len(feed_entry.content) > 0:
                    content_item = feed_entry.content[0]
                    if isinstance(content_item, dict):
                        content_html = content_item.get('value')
                    elif hasattr(content_item, 'value'):
                        content_html = content_item.value

                if not content_html and feed_entry.get('summary'):
                    content_html = feed_entry.summary
            
            if content_html:
                soup = BeautifulSoup(content_html, 'html.parser')
                p_tags = soup.find_all('p')
                if p_tags:
                    content_text = ' '.join(p.get_text(separator=' ', strip=True) for p in p_tags if p.get_text(strip=True))
                else:
                    content_text = soup.get_text(separator=' ', strip=True)
                content_text = content_text.strip() if content_text else None

            if not content_text:
                self.logger.info(f"Content from feed was empty or insufficient for {response.url}. Falling back to XPath.")
                xpath_expression = '//*[@id="main-section"]/section/div[1]/div/div[1]/div/div/div/div/span[2]/p//text()' # Tribune specific XPath
                content_list = response.xpath(xpath_expression).getall()
                if content_list:
                    processed_segments = [segment.strip() for segment in content_list if segment.strip()]
                    content_text = ' '.join(processed_segments)
                    if not content_text.strip(): # Check if joined string is empty
                         content_text = None
                else:
                    self.logger.warning(f"Content not found via XPath for {response.url}")
                    content_text = None
            
            item['content'] = content_text.strip() if content_text else None
            # End of content extraction logic

            # Clean other text fields
            item['heading'] = item['heading'].strip() if item['heading'] else None
            item['author'] = item['author'].strip() if item['author'] else None
            # item['category'] is already stripped or None
            # item['content'] is already stripped or None
            
            publish_date = None
            if date_str_for_parsing:
                try:
                    if hasattr(feed_entry, 'published_parsed') and feed_entry.published_parsed:
                        publish_date = datetime(*feed_entry.published_parsed[:6])
                    elif date_str_for_parsing:
                        parsing_val = date_str_for_parsing
                        if parsing_val.endswith('Z'):
                            parsing_val = parsing_val[:-1] + '+00:00'
                            publish_date = datetime.fromisoformat(parsing_val)
                        else:
                            if len(parsing_val) > 6 and parsing_val[-3] == ':':
                                parsing_val = parsing_val[:-3] + parsing_val[-2:]
                            publish_date = datetime.fromisoformat(parsing_val)
                except ValueError:
                    common_formats = ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]
                    for fmt in common_formats:
                        try:
                            publish_date = datetime.strptime(date_str_for_parsing, fmt)
                            self.logger.info(f"Parsed date '{date_str_for_parsing}' using strptime format '{fmt}'.")
                            break
                        except ValueError:
                            continue
                    if not publish_date:
                        self.logger.warning(f"Could not parse date: {original_date_str} with any known format.")
                except Exception as e_date:
                     self.logger.error(f"Unexpected error parsing date '{original_date_str}': {e_date}")
            
            self.mark_article_scraped(response.url)
            self.stats['articles_scraped'] += 1
            self.logger.info(f"Scraped Tribune article: {item['heading']} from {response.url}")

            yield item

        except Exception as e:
            self.logger.error(f"Error parsing Tribune article {response.url}: {str(e)}")
            self.stats['errors'] += 1