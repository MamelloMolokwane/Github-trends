from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pandas as pd
import datetime
import requests
import sqlite3
import json
import csv
import os

load_dotenv()
TOKEN = os.getenv("MY_TOKEN")

def main():
    bronze_layer = f"./data/bronze/raw_repo_{datetime.date.today().isoformat()}.json"
    silver_layer = f"./data/silver/cleaned_repo_{datetime.date.today()}.csv"
    gold_layer = "./data/gold/github-trends.db"
    os.makedirs(os.path.dirname(gold_layer), exist_ok=True)

    extract(bronze_layer)

    print("Finished with extraction moving on to transformation...")

    transform(bronze_layer, silver_layer)
    print("Finished with transformation moving on loading dimension...")

    load_dimensions(silver_layer, gold_layer)
    print("Finished loading dimensions, moving on too loading facts...")

    load_facts(silver_layer, gold_layer)
    print("Finished loading facts. Pipeline loaded.")
    table_check(gold_layer)
    print("Warehouse created.")
    
def table_check(database):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    tables = [
        "dim_repository",
        "dim_language",
        "dim_owner",
        "dim_date",
        "fact_repo_snapshot"
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count}")

    conn.close()
    

def get_raw_data(file_loc):
    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "Application/vnd.github+json"
    }
    # Get repositories from the last 3 months
    last_month = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    params = {
        "q": f"created:>{last_month}", # Measure by new repositories.
        "sort": "stars",
        "order": "desc",
        "per_page": 100
    }
    response = requests.get(url, params=params, headers=headers, timeout=14)
    
    if response.status_code == 200:
        os.makedirs(os.path.dirname(file_loc), exist_ok=True)
        with open(file_loc, "w") as file:
            json.dump(response.json(), file, indent=4)
    else:
        print("Problem occoured get_raw_data returned with statuse code:", response.status_code)
        print(response.text)

def extract(file_loc):
    get_raw_data(file_loc)
    try:
        with open(file_loc, encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("File probably not created.")
        return f"{file_loc} not found"
        
    
    
def transform(raw_loc, cleaned_loc):
    # Transform and clean the data then save it in the silver layer
    cleaned_data = []
    # os.makedirs(os.path.dirname())

    with open(raw_loc, encoding="utf-8") as file:
        raw_data = json.load(file)

    for data in raw_data["items"]:
        clean = {
            "repository_id": data["id"],
            "repository_name": data["name"].strip(),
            "repository_link": data["html_url"].strip(),
            "owner_id": data["owner"]["id"],
            "owner_name": data["owner"]["login"].strip(),
            "owner_type": data["owner"]["type"].strip(),
            "description": (data["description"] or "").strip(),
            "stars": data["stargazers_count"],
            "fork_count": data["forks_count"],
            "language": (data["language"] or "Unknown").strip(),
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "watchers_count": data["watchers_count"],
            "snapshot_date": datetime.date.today().isoformat(),
            "open_issues_count": data["open_issues_count"],
            "archived": data["archived"],
            "fork": data["fork"],
            "topics": json.dumps(data["topics"])
        }

        if clean not in cleaned_data:
            cleaned_data.append(clean)
    
    headers = [
        "repository_id",
        "repository_name",
        "repository_link",
        "owner_id",
        "owner_name",
        "owner_type",
        "description",
        "stars",
        "fork_count",
        "language",
        "created_at",
        "updated_at",
        "watchers_count",
        "snapshot_date",
        "open_issues_count",
        "archived",
        "fork",
        "topics",
    ]

    # Save in csv file
    os.makedirs(os.path.dirname(cleaned_loc), exist_ok=True)
    with open(cleaned_loc, "w",  newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(cleaned_data)

    print("Data has been transformed and put into the silver the layer.")

# Create function to get repos
def get_silver_layer_data(silver_layer):   
    with open(silver_layer, encoding="utf-8") as silver:
        reader = list(csv.DictReader(silver))
    return reader

def load_facts(cleaned_loc, database):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    silver_layer = get_silver_layer_data(cleaned_loc)

    # Create table
    create_table = """
    CREATE TABLE IF NOT EXISTS fact_repo_snapshot (
        snapshot_key INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_key INTEGER NOT NULL REFERENCES dim_repository(repo_key),
        language_key INTEGER NOT NULL REFERENCES dim_language(language_key),
        owner_key INTEGER NOT NULL REFERENCES dim_owner(owner_key),
        date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
        repo_id INTEGER,
        stars INTEGER,
        forks INTEGER,
        watchers INTEGER,
        UNIQUE(repo_key, date_key)
    )
        """
    cursor.execute(create_table)

    # Insert data into table
    for row in silver_layer:
        cursor.execute("""
        SELECT repo_key FROM dim_repository WHERE repo_id = ?
        """, (row["repository_id"],))
        repo_key = cursor.fetchone()["repo_key"]

        cursor.execute("""
        SELECT owner_key FROM dim_owner WHERE owner_id = ?
        """, (row["owner_id"],))
        owner_key = cursor.fetchone()["owner_key"]

        cursor.execute("""
        SELECT language_key FROM dim_language WHERE language_name = ?
        """, (row["language"],))
        language_key = cursor.fetchone()["language_key"]
        # 
        d = datetime.datetime.fromisoformat(row["snapshot_date"])
        cursor.execute("""
        SELECT date_key FROM dim_date WHERE year = ? AND month = ? AND DAY = ?
        """, (d.year, d.month, d.day))
        date_key = cursor.fetchone()["date_key"]

        # Load fact_repo_snapshot table
        cursor.execute("""
        INSERT INTO fact_repo_snapshot (repo_key, repo_id, owner_key, language_key, date_key, stars, forks, watchers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(repo_key, date_key)
        DO UPDATE SET
        stars = excluded.stars,
        forks = excluded.forks,
        watchers = excluded.watchers
        """, (repo_key, row["repository_id"], owner_key, language_key, date_key, row["stars"], row["fork_count"], row["watchers_count"])
        )

    conn.commit()
    conn.close()
    

def load_dimensions(cleaned_loc, database):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create Dimension tables
    dim_repo = """
    CREATE TABLE IF NOT EXISTS dim_repository (
    repo_key INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER UNIQUE,
    repo_name TEXT
    )
        """
    dim_language = """
    CREATE TABLE IF NOT EXISTS dim_language (
    language_key INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT UNIQUE
    )
        """
    dim_owner = """
    CREATE TABLE IF NOT EXISTS dim_owner (
    owner_key INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_name TEXT,
    owner_id INTEGER UNIQUE,
    owner_type TEXT
    )
        """
    dim_date = """
    CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    UNIQUE(year, month, day)
    )
    """
    cursor.execute(dim_repo)
    cursor.execute(dim_owner)
    cursor.execute(dim_language)
    cursor.execute(dim_date)

    # Get data to insert into tables
    silver_data = get_silver_layer_data(cleaned_loc)
    for data in silver_data:
        # Insert the correct data into it's correct table
        
        # Insert language into dim_language
        cursor.execute("""
        INSERT OR IGNORE INTO dim_language (language_name)
        VALUES (?)
        """, (data["language"],))
        # Insert repository data into dim_repo
        cursor.execute("""
        INSERT OR IGNORE INTO dim_repository (repo_id, repo_name)
        VALUES (?, ?)""", (int(data["repository_id"]), data["repository_name"])
        )
        # Insert owner data into dim_owner 
        cursor.execute("""
        INSERT OR IGNORE INTO dim_owner (owner_name, owner_id, owner_type)
        VALUES (?, ?, ?)""", (data["owner_name"], int(data["owner_id"]), data["owner_type"])
        )
        # Insert date data into dim_date
        d = datetime.datetime.fromisoformat(data["snapshot_date"])
        cursor.execute("""
        INSERT OR IGNORE INTO dim_date (year, month, day)
        VALUES (?, ?, ?)""", (d.year, d.month, d.day)
        )

    # Commit and close sqlite
    conn.commit()
    conn.close()
        
    

if __name__ == "__main__":
    main()