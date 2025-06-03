import pytest
from datetime import datetime, timezone
from scrapy.exceptions import DropItem

# Adjust imports based on your project structure
from news_scrapper.news_scrapper.items import NewsArticleItem
from news_scrapper.news_scrapper.pipelines import NewsValidationPipeline # Assuming this is where your pipeline is

# Mock a spider for pipeline testing
class MockSpider:
    def __init__(self, name='test_spider'):
        self.name = name
        # Add any other spider attributes your pipeline might access, e.g., logger
        class MockLogger:
            def warning(self, msg, *args, **kwargs): pass
            def info(self, msg, *args, **kwargs): pass
            def error(self, msg, *args, **kwargs): pass
            def debug(self, msg, *args, **kwargs): pass
        self.logger = MockLogger()


@pytest.fixture
def valid_item_data():
    return {
        'url': 'http://example.com/valid',
        'heading': 'Valid Heading',
        'content': 'Valid content for the article.',
        'author': 'Test Author',
        'date': '2025-01-01T12:00:00Z', # ISO format string
        'category': 'News'
    }

@pytest.fixture
def mock_spider_instance():
    return MockSpider()

def test_validation_pipeline_valid_item(valid_item_data, mock_spider_instance):
    pipeline = NewsValidationPipeline()
    item = NewsArticleItem(**valid_item_data)

    processed_item = pipeline.process_item(item, mock_spider_instance)

    assert processed_item is item # Should return the same item if valid
    assert 'spider_name' in processed_item
    assert processed_item['spider_name'] == mock_spider_instance.name
    assert 'processed_at' in processed_item
    assert isinstance(processed_item['processed_at'], str) # Assuming it's an ISO string

def test_validation_pipeline_missing_heading(valid_item_data, mock_spider_instance):
    pipeline = NewsValidationPipeline()
    invalid_item_data = valid_item_data.copy()
    del invalid_item_data['heading'] # Make it invalid
    # Need to handle potential None for fields not present if NewsArticleItem uses defaults
    item = NewsArticleItem()
    for key, value in invalid_item_data.items():
        item[key] = value
    if 'heading' not in item: # Ensure heading is truly missing or None
        item['heading'] = None

    with pytest.raises(DropItem) as excinfo:
        pipeline.process_item(item, mock_spider_instance)
    assert "Missing heading in" in str(excinfo.value)

def test_validation_pipeline_missing_content(valid_item_data, mock_spider_instance):
    pipeline = NewsValidationPipeline()
    invalid_item_data = valid_item_data.copy()
    invalid_item_data['content'] = None # Make it invalid
    item = NewsArticleItem()
    for key, value in invalid_item_data.items():
        item[key] = value

    with pytest.raises(DropItem) as excinfo:
        pipeline.process_item(item, mock_spider_instance)
    assert "Missing content in" in str(excinfo.value)

def test_validation_pipeline_strips_fields(mock_spider_instance):
    pipeline = NewsValidationPipeline()
    item_data_with_whitespace = {
        'url': ' http://example.com/whitespace ', # URLs are typically not stripped by this kind of pipeline
        'heading': '  Whitespace Heading  ',
        'content': '  Content with spaces.  ',
        'author': '  Author Name  ',
        'date': '  2025-01-02T10:00:00Z  ',
        'category': '  Category Name  '
    }
    item = NewsArticleItem(**item_data_with_whitespace)

    processed_item = pipeline.process_item(item, mock_spider_instance)

    assert processed_item['url'] == ' http://example.com/whitespace ' # URLs are typically not stripped
    assert processed_item['heading'] == 'Whitespace Heading'
    assert processed_item['content'] == 'Content with spaces.'
    assert processed_item['author'] == 'Author Name'
    assert processed_item['date'] == '2025-01-02T10:00:00Z' # Assuming date string is also stripped
    assert processed_item['category'] == 'Category Name'

def test_validation_pipeline_empty_optional_fields(valid_item_data, mock_spider_instance):
    pipeline = NewsValidationPipeline()
    item_data = valid_item_data.copy()
    item_data['author'] = None
    item_data['category'] = ''
    item = NewsArticleItem(**item_data)

    processed_item = pipeline.process_item(item, mock_spider_instance)
    assert processed_item is item
    assert processed_item['author'] is None
    assert processed_item['category'] == ''

# Note: JsonExportPipeline tests are more complex due to file interactions
# and might require mocking file system operations or checking actual file output,
# which is beyond "basic" unit tests for this context.
# If JsonExportPipeline has complex logic beyond just writing to a file,
# that logic could be unit tested by mocking the file writing part.
