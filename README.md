# NEWS_Project

A Python-based news scraping and analysis project that collects and processes news articles from various sources. This project uses **Scrapy** for web scraping and performs sentiment analysis and other NLP-based assessments on the collected data.

## Features

- Scrapes news articles from websites like [Dawn](https://www.dawn.com) and [Tribune](https://www.tribune.com).
- Stores scraped articles in a SQLite database.
- Logs activity and errors for debugging purposes.
- Includes scripts for running crawlers in parallel.
- Prepares data for sentiment analysis and NLP tasks (future enhancement).

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- Virtualenv (optional but recommended)

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/waleedkaimkhani/NEWS_Project.git
   cd NEWS_Project
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up Scrapy:
   Ensure Scrapy is properly configured by checking the `scrapy.cfg` file in the root directory.

## Usage

### Running the Crawlers

#### 1. Run Individual Spiders

To run a specific spider (e.g., the Dawn spider):

```bash
scrapy crawl dawn_spider
```

#### 2. Run Parallel Spiders

To run multiple spiders in parallel, use the `parallel_scrape.py` script:

```bash
python news_scrapper/parallel_scrape.py
```

### Logging
Logs are stored in the `logs/` directory and include timestamps for easier debugging. Each run creates a new log file based on the current date.

### Database
Scraped articles are stored in a SQLite database named `scraped_articles.db`. Use a SQLite browser or Python to query the database.

### Configuration
Adjust settings in `news_scrapper/settings.py` to modify Scrapy configurations like download delay, user agent, etc.

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
|├── data/                   # Directory for log files
|├── stats/                   # Directory for log files
|├── scraped_articles.db     # SQLite database for storing articles
|├── requirements.txt        # Python dependencies
|├── scrapy.cfg              # Scrapy configuration file
```

## Contributing

1. Fork the repository.
2. Create a new branch for your feature/bugfix:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of changes"
   ```
4. Push to your forked repository:
   ```bash
   git push origin feature-name
   ```
5. Submit a pull request.

## Future Enhancements

- Sentiment analysis of scraped articles.
- Bias and propaganda detection using NLP models.
- Integration with a dashboard to visualize trends in news sentiment.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Scrapy](https://scrapy.org/) for the web scraping framework.
- Local news websites for providing data.

---

Feel free to contribute or raise issues to improve this project!

