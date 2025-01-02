# NEWS Project

A web scraping project built with Scrapy to collect news articles from Pakistani news websites (Dawn and Tribune), automated using Prefect.

## Features

- Scrapes news articles from websites like [Dawn](https://www.dawn.com) and [Tribune](https://www.tribune.com).
- Redis-based URL deduplication with 24-hour expiry
- JSON export of scraped articles
- Detailed logging system
- Daily statistics tracking
- Automated workflow using Prefect
- Scheduled article scraping

## Requirements

- Python 3.7+
- Redis
- Docker (recommended) or WSL2 for Windows users
- Prefect

## Installation

```bash
# Clone repository
git clone https://github.com/waleedkaimkhani/NEWS_Project.git
cd NEWS_Project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start Redis
docker run --name redis -p 6379:6379 -d redis

# Start Prefect server
prefect server start
```

## Usage

### Manual Spider Execution
```bash
scrapy crawl dawn_latest
scrapy crawl tribune_latest
```


#### Run Parallel Spiders

To run multiple spiders in parallel, use the `parallel_scrape.py` script:

```bash
python news_scrapper/parallel_scrape.py
```

### Automated Pipeline
```bash
# Start Prefect agent
prefect agent start -q default

# Deploy workflow
python deployment.py

# View runs in Prefect UI
http://localhost:4200
```

## Prefect Pipeline

The project uses Prefect for workflow automation:
- Scheduled scraping every 12 hours
- Parallel execution of spiders
- Error handling and retries
- Email notifications for failures
- Monitoring through Prefect UI

## Output

- Articles saved as JSON in `data/` directory
- Logs stored in `logs/` directory
- Statistics saved in `stats/` directory
- Pipeline runs visible in Prefect UI

## Project Structure

```

## Project Structure

```
NEWS_Project/
|├── news_scrapper/
|   |├── spiders/             # Spiders for scraping websites
|   |├── items.py            # Defines data models for scraped items
|   |├── pipelines.py        # Data processing pipelines
|   |├── settings.py         # Scrapy project settings
|   |├── middlewares.py      # Middleware for custom behaviors
|   |├── parallel_scrape.py  # Script to run spiders in parallel
|├── logs/                   # Directory for log files
|├── data/                   # Directory where json are stored
|├── stats/                  # Directory where stats for e.g no of articles scrapped
|├── news_pipeline.py        # prefect pipeline which run scrapper and then stores data in postgress db
|├── deployment.py           # prefect flow scheduling script 
|├── requirements.txt        # Python dependencies
|├── scrapy.cfg              # Scrapy configuration file
```


## Future Enhancements

- Sentiment analysis of scraped articles.
- Bias and propaganda detection using NLP models.
- Integration with a dashboard to visualize trends in news sentiment.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Scrapy](https://scrapy.org/) for the web scraping framework.
- Local news websites for providing data.
- prefect for open source workflow orchectration
- postgress for open source relational DB
---

Feel free to contribute or raise issues to improve this project!

