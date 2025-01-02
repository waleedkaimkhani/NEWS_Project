import json
import psycopg2
import os

# Database connection details
DB_NAME = "news_db"
DB_USER = "admin"
DB_PASSWORD = "admin123"
DB_HOST = "localhost"
DB_PORT = "5432"

# Directory containing JSON files
JSON_DIR = "./data/articles"

# Connect to PostgreSQL
try:
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = connection.cursor()

    # Create table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS news (
        id SERIAL PRIMARY KEY,
        heading TEXT,
        content TEXT,
        author TEXT,
        date DATE,
        category TEXT,
        url TEXT,
        processed_at TIMESTAMP,
        spider_name TEXT
    );
    """
    cursor.execute(create_table_query)

    # Iterate over all JSON files in the directory
    for filename in os.listdir(JSON_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(JSON_DIR, filename)
            print(f"Processing file: {file_path}")
            
            # Load JSON data
            with open(file_path, "r") as file:
                news_data = json.load(file)

            # Insert data into the table
            insert_query = """
            INSERT INTO news (heading, content, author, date, category, url, processed_at, spider_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            for article in news_data:
                cursor.execute(insert_query, (
                    article.get("heading"),
                    article.get("content"),
                    article.get("author"),
                    article.get("date"),
                    article.get("category"),
                    article.get("url"),
                    article.get("processed_at"),
                    article.get("spider_name")
                ))

    # Commit changes
    connection.commit()
    print("All data inserted successfully!")

except Exception as e:
    print("An error occurred:", e)

finally:
    if connection:
        cursor.close()
        connection.close()
