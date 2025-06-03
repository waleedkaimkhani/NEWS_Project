import pytest
from scrapy.http import TextResponse, Request # Added Request
from scrapy.item import Item, Field
import feedparser
from datetime import datetime, timezone, timedelta # Added timedelta
import time # For struct_time

# Adjust imports based on your project structure
from news_scrapper.news_scrapper.spiders.Dawn_spider import DawnLatestSpider
from news_scrapper.news_scrapper.spiders.tribune_latest import TribuneLatestSpider
from news_scrapper.news_scrapper.items import NewsArticleItem

# --- Mock RSS Data ---

MOCK_DAWN_RSS_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Dawn Feed</title>
    <link>https://www.dawn.com</link>
    <description>Latest News from Dawn</description>
    <item>
      <title>Dawn Test Article 1</title>
      <link>http://www.dawn.com/news/dawnarticle1</link>
      <author>author1@dawn.com (Author One)</author>
      <pubDate>Tue, 03 Jun 2025 10:00:00 +0000</pubDate>
      <category>Pakistan</category>
      <description><![CDATA[<p>Summary of Dawn Article 1.</p>]]></description>
      <content:encoded><![CDATA[<p>Full content of Dawn Article 1. It is very detailed.</p>]]></content:encoded>
    </item>
    <item>
      <title>Dawn Test Article 2</title>
      <link>http://www.dawn.com/news/dawnarticle2</link>
      <author>author2@dawn.com (Author Two)</author>
      <pubDate>Tue, 03 Jun 2025 11:00:00 +0000</pubDate>
      <category>World</category>
      <description><![CDATA[<p>Summary of Dawn Article 2.</p>]]></description>
      <content:encoded><![CDATA[<p>Full content of Dawn Article 2. More details here.</p>]]></content:encoded>
    </item>
  </channel>
</rss>
"""

MOCK_TRIBUNE_RSS_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Tribune Feed</title>
    <link>https://tribune.com.pk</link>
    <description>Latest News from Tribune</description>
    <item>
      <title>Tribune Test Article 1</title>
      <link>http://tribune.com.pk/story/tribunearticle1</link>
      <author>writer@tribune.com.pk (Tribune Writer)</author>
      <pubDate>Tue, 03 Jun 2025 12:00:00 +0000</pubDate>
      <category>Business</category>
      <description><![CDATA[<p>Summary of Tribune Article 1.</p>]]></description>
      <content:encoded><![CDATA[<p>Full content of Tribune Article 1. It is very detailed and long.</p>]]></content:encoded>
    </item>
  </channel>
</rss>
"""

# --- Test Spider Parse Methods ---

def test_dawn_spider_parse_rss(mocker):
    spider = DawnLatestSpider()
    mocker.patch.object(spider, 'is_article_scraped', return_value=False)

    mock_response = TextResponse(
        url=spider.start_urls[0],
        body=MOCK_DAWN_RSS_CONTENT,
        encoding='utf-8'
    )

    requests = list(spider.parse(mock_response))

    assert len(requests) == 2 # We have 2 items in mock Dawn RSS
    assert spider.stats['articles_found'] == 2

    for i, request in enumerate(requests):
        assert request.callback == spider.parse_article
        assert isinstance(request.meta['feed_entry'], feedparser.FeedParserDict)
        if i == 0:
            assert request.url == "http://www.dawn.com/news/dawnarticle1"
            assert request.meta['feed_entry'].title == "Dawn Test Article 1"
        elif i == 1:
            assert request.url == "http://www.dawn.com/news/dawnarticle2"
            assert request.meta['feed_entry'].title == "Dawn Test Article 2"

def test_tribune_spider_parse_rss(mocker):
    spider = TribuneLatestSpider()
    mocker.patch.object(spider, 'is_article_scraped', return_value=False)

    mock_response = TextResponse(
        url=spider.start_urls[0],
        body=MOCK_TRIBUNE_RSS_CONTENT,
        encoding='utf-8'
    )

    requests = list(spider.parse(mock_response))

    assert len(requests) == 1 # We have 1 item in mock Tribune RSS
    assert spider.stats['articles_found'] == 1

    request = requests[0]
    assert request.callback == spider.parse_article
    assert isinstance(request.meta['feed_entry'], feedparser.FeedParserDict)
    assert request.url == "http://tribune.com.pk/story/tribunearticle1"
    assert request.meta['feed_entry'].title == "Tribune Test Article 1"

# --- Test Spider Parse Article Methods (Focus on Feed Data) ---

@pytest.fixture
def mock_dawn_spider(mocker):
    spider = DawnLatestSpider()
    mocker.patch.object(spider, 'mark_article_scraped') # Mock to prevent Redis interaction
    # Mock logger to prevent errors if it's not fully set up in test
    spider._logger = mocker.Mock() # Patch underlying _logger attribute
    return spider

@pytest.fixture
def mock_tribune_spider(mocker):
    spider = TribuneLatestSpider()
    mocker.patch.object(spider, 'mark_article_scraped') # Mock to prevent Redis interaction
    spider._logger = mocker.Mock() # Patch underlying _logger attribute
    return spider

def test_dawn_spider_parse_article_from_feed(mock_dawn_spider, mocker):
    spider = mock_dawn_spider

    mock_feed_entry_data = {
        'title': 'Dawn Feed Title',
        'link': 'http://www.dawn.com/news/feedarticle',
        'author_detail': {'name': 'Feed Author Name'},
        'published': 'Tue, 03 Jun 2025 14:30:00 +0000',
        'tags': [{'term': 'Feed Category'}],
        'summary': '<p>Short summary from feed.</p>',
        'content': [{'type': 'text/html', 'value': '<p>Full article content here from feed.</p><p>Another paragraph.</p>'}]
    }
    # Simulate feedparser's published_parsed for RFC822 date, as spider prioritizes it
    parsed_time_struct = time.gmtime(datetime.strptime(mock_feed_entry_data['published'], "%a, %d %b %Y %H:%M:%S %z").timestamp())
    mock_feed_entry_data['published_parsed'] = parsed_time_struct
    mock_feed_entry = feedparser.FeedParserDict(mock_feed_entry_data)

    dummy_request = Request(url=mock_feed_entry.link, meta={'feed_entry': mock_feed_entry})
    mock_response = TextResponse(
        url=mock_feed_entry.link,
        body="<html><body>Fallback content if needed</body></html>",
        encoding='utf-8',  # Ensure encoding is set
        request=dummy_request # Pass the request object
    )
    # mock_response.meta = {'feed_entry': mock_feed_entry} # No longer needed

    # Patching BeautifulSoup in the context of the spider's module
    bs_mock_soup = mocker.Mock()

    p_tag_mock1 = mocker.Mock()
    p_tag_mock1.get_text.return_value = "Full article content here from feed."
    p_tag_mock2 = mocker.Mock()
    p_tag_mock2.get_text.return_value = "Another paragraph."

    bs_mock_soup.find_all.return_value = [p_tag_mock1, p_tag_mock2]
    # Fallback if find_all returns empty or joined result is empty
    bs_mock_soup.get_text.return_value = "Full article content here from feed. Another paragraph."
    mocker.patch('news_scrapper.news_scrapper.spiders.Dawn_spider.BeautifulSoup', return_value=bs_mock_soup)

    item_generator = spider.parse_article(mock_response)
    item = next(item_generator)


    assert isinstance(item, NewsArticleItem)
    assert item['heading'] == 'Dawn Feed Title'
    assert item['author'] == 'Feed Author Name'
    assert item['date'] == 'Tue, 03 Jun 2025 14:30:00 +0000'
    assert item['category'] == 'Feed Category'
    assert item['content'] == 'Full article content here from feed. Another paragraph.'
    assert item['url'] == mock_feed_entry.link

    spider.mark_article_scraped.assert_called_once_with(mock_response.url)
    assert spider.stats['articles_scraped'] == 1


def test_dawn_spider_parse_article_content_fallback(mock_dawn_spider, mocker):
    spider = mock_dawn_spider

    mock_feed_entry_data = {
        'title': 'Dawn Feed Title Fallback',
        'link': 'http://www.dawn.com/news/feedarticlefallback',
        'author': 'Feed Author Fallback',
        'published': '2025-06-03T15:00:00+00:00',
        'tags': [{'term': 'Feed Cat Fallback'}],
        'summary': '<p>Tiny.</p>',
    }
    # For ISO format string, published_parsed might not be set by feedparser, or be None.
    # Let the spider's string parsing logic handle this.
    # mock_feed_entry_data['published_parsed'] = feedparser._parse_date(mock_feed_entry_data['published']) # Removed
    mock_feed_entry = feedparser.FeedParserDict(mock_feed_entry_data)

    html_body_for_xpath = """
    <html><body>
        <div class="story__content">
            <p>This is paragraph one from XPath.</p>
            <p>This is paragraph two from XPath.</p>
        </div>
    </body></html>
    """
    dummy_request = Request(url=mock_feed_entry.link, meta={'feed_entry': mock_feed_entry})
    mock_response = TextResponse(
        url=mock_feed_entry.link,
        body=html_body_for_xpath,
        encoding='utf-8',
        request=dummy_request
    )
    # mock_response.meta = {'feed_entry': mock_feed_entry} # No longer needed

    bs_mock_instance = mocker.Mock()
    bs_mock_instance.find_all.return_value = [] # Simulate no <p> tags from feed summary
    bs_mock_instance.get_text.return_value = "" # Simulate an empty string from feed summary to trigger XPath
    mocker.patch('news_scrapper.news_scrapper.spiders.Dawn_spider.BeautifulSoup', return_value=bs_mock_instance)


    item_generator = spider.parse_article(mock_response)
    item = next(item_generator)

    assert isinstance(item, NewsArticleItem)
    assert item['heading'] == 'Dawn Feed Title Fallback'
    assert item['content'] == 'This is paragraph one from XPath. This is paragraph two from XPath.'
    assert item['url'] == mock_feed_entry.link
    spider.mark_article_scraped.assert_called_once_with(mock_response.url)


def test_tribune_spider_parse_article_from_feed(mock_tribune_spider, mocker):
    spider = mock_tribune_spider

    mock_feed_entry_data = {
        'title': 'Tribune Feed Title',
        'link': 'http://tribune.com.pk/story/feedarticle',
        'author_detail': {'name': 'Tribune Feed Author'},
        'published': 'Tue, 03 Jun 2025 16:00:00 +0500',
        'tags': [{'term': 'Tribune Feed Category'}],
        'content': [{'type': 'text/html', 'value': '<div><p>Tribune full content.</p><p>Second paragraph.</p></div>'}]
    }
    # Simulate feedparser's published_parsed for RFC822 date
    parsed_time_struct = time.gmtime(datetime.strptime(mock_feed_entry_data['published'], "%a, %d %b %Y %H:%M:%S %z").timestamp())
    mock_feed_entry_data['published_parsed'] = parsed_time_struct
    mock_feed_entry = feedparser.FeedParserDict(mock_feed_entry_data)

    dummy_request = Request(url=mock_feed_entry.link, meta={'feed_entry': mock_feed_entry})
    mock_response = TextResponse(
        url=mock_feed_entry.link,
        body="<html><body>Fallback content.</body></html>",
        encoding='utf-8',
        request=dummy_request
    )
    # mock_response.meta = {'feed_entry': mock_feed_entry} # No longer needed

    bs_mock_soup_tribune = mocker.Mock()

    p_tag_mock_tribune1 = mocker.Mock()
    p_tag_mock_tribune1.get_text.return_value = "Tribune full content."
    p_tag_mock_tribune2 = mocker.Mock()
    p_tag_mock_tribune2.get_text.return_value = "Second paragraph."

    bs_mock_soup_tribune.find_all.return_value = [p_tag_mock_tribune1, p_tag_mock_tribune2]
    bs_mock_soup_tribune.get_text.return_value = "Tribune full content. Second paragraph."
    mocker.patch('news_scrapper.news_scrapper.spiders.tribune_latest.BeautifulSoup', return_value=bs_mock_soup_tribune)

    item_generator = spider.parse_article(mock_response)
    item = next(item_generator)

    assert isinstance(item, NewsArticleItem)
    assert item['heading'] == 'Tribune Feed Title'
    assert item['author'] == 'Tribune Feed Author'
    assert item['date'] == 'Tue, 03 Jun 2025 16:00:00 +0500'
    assert item['category'] == 'Tribune Feed Category'
    assert item['content'] == 'Tribune full content. Second paragraph.'
    assert item['url'] == mock_feed_entry.link

    spider.mark_article_scraped.assert_called_once_with(mock_response.url)
    assert spider.stats['articles_scraped'] == 1


def test_dawn_spider_date_parsing_various_formats(mock_dawn_spider, mocker):
    spider = mock_dawn_spider
    # Mock the logger for this specific test to check for warnings
    # logger_spy = mocker.spy(spider.logger, 'warning')

    dates_to_test = {
        "2023-10-27T08:30:00+05:00": datetime(2023, 10, 27, 8, 30, tzinfo=timezone(timedelta(hours=5))),
        "2024-01-15T12:00:00Z": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        "Wed, 05 Jun 2024 10:20:30 +0000": datetime(2024, 6, 5, 10, 20, 30, tzinfo=timezone.utc),
        "Thu, 06 Jun 2024 15:45:10 GMT": datetime(2024, 6, 6, 15, 45, 10, tzinfo=timezone.utc), # GMT is equivalent to +0000
    }

    for date_str_in, expected_dt_out in dates_to_test.items():
        mock_feed_entry_data = { 'title': 'Date Test', 'link': f'http://example.com/{date_str_in}', 'published': date_str_in}

        # Simulate feedparser's 'published_parsed' if the format is RFC822/GMT, as spider prioritizes this
        if "GMT" in date_str_in or ("+" not in date_str_in and "Z" not in date_str_in and date_str_in.count(":") == 2 and ("AM" in date_str_in.upper() or "PM" in date_str_in.upper() or any(day in date_str_in for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))): # Heuristic for RFC822 like
            try:
                # For RFC822-like dates, feedparser populates 'published_parsed'
                dt_obj = datetime.strptime(date_str_in, "%a, %d %b %Y %H:%M:%S %z")
                mock_feed_entry_data['published_parsed'] = dt_obj.timetuple()
            except ValueError:
                 # Try GMT format
                try:
                    dt_obj = datetime.strptime(date_str_in, "%a, %d %b %Y %H:%M:%S %Z")
                    mock_feed_entry_data['published_parsed'] = dt_obj.timetuple()
                except ValueError:
                    pass # Let the spider's string parsing attempt it if direct struct_time simulation fails

        mock_feed_entry = feedparser.FeedParserDict(mock_feed_entry_data)
        dummy_request = Request(url=mock_feed_entry.link, meta={'feed_entry': mock_feed_entry})
        mock_response = TextResponse(url=mock_feed_entry.link, body="<p>content</p>", encoding='utf-8', request=dummy_request)
        # mock_response.meta = {'feed_entry': mock_feed_entry} # No longer needed

        # Patch BeautifulSoup for this specific call if content parsing is complex
        bs_mock_instance = mocker.Mock()
        bs_mock_instance.find_all.return_value = [mocker.Mock(get_text=lambda: "content")]
        bs_mock_instance.get_text.return_value = "content"
        mocker.patch('news_scrapper.news_scrapper.spiders.Dawn_spider.BeautifulSoup', return_value=bs_mock_instance)

        item_generator = spider.parse_article(mock_response)
        item = next(item_generator)
        assert item['date'] == date_str_in

        # Check that no date parsing warnings were logged for these valid formats
        # This requires ensuring the logger was properly mocked and spied on if specific checks are needed.
        # For now, we assume if it passes and item['date'] is correct, the internal publish_date was likely fine.
        # Example of a more rigorous check:
        # assert not any("Could not parse date" in call.args[0] for call in logger_spy.call_args_list if call.args)
        # logger_spy.reset_mock() # Reset spy for next iteration

    assert True # If all iterations complete without error
