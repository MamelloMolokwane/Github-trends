from psycopg.rows import dict_row
from dotenv import load_dotenv
import pandas as pd
import datetime
import requests
import psycopg
import json
import csv
import os

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

def main():
    bronze_layer = f"./data/bronze/raw_repo_{datetime.date.today().isoformat()}.json"
    silver_layer = f"./data/silver/cleaned_repo_{datetime.date.today()}.csv"
    # gold_layer = "./data/gold/github-trends.db"
    # os.makedirs(os.path.dirname(gold_layer), exist_ok=True)

    extract(bronze_layer)

    print("Finished with extraction moving on to transformation...")

    transform(bronze_layer, silver_layer)
    print("Finished with transformation moving on loading dimension...")

    load_dimensions(silver_layer)
    print("Finished loading dimensions, moving on too loading facts...")

    load_facts(silver_layer)
    print("Finished loading facts. Pipeline loaded.")
    table_check()
    print("Warehouse created.")

def get_database():
    return psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    row_factory=dict_row)

    
def table_check():
    conn = get_database()
    cursor = conn.cursor()
    tables = [
        "dim_repository",
        "dim_language",
        "dim_owner",
        "dim_date",
        "fact_repo_snapshot"
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*)  AS count FROM {table}")
        count = cursor.fetchone()["count"]
        print(f"{table}: {count}")

    conn.close()
    

def get_raw_data(file_loc):
    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "Application/vnd.github+json"
    }
    # Get repositories created in the last 24 hours.
    day = (datetime.date.today() - datetime.timedelta(1)).isoformat() # Maybe turn this back into month.
    params = {
        "q": f"created:>{day}", # Measure by new repositories.
        "sort": "stars",
        "order": "desc",
        "per_page": 100
    }
    response = requests.get(url, params=params, headers=headers, timeout=14)
    
    if response.status_code == 200:
        os.makedirs(os.path.dirname(file_loc), exist_ok=True)
        with open(file_loc, "w") as file:
            json.dump(response.json(), file, indent=4)
        # print(response.json())
    else:
        print("Problem occoured get_raw_data returned with statuse code:", response.status_code)
        print(response.text)

def extract(file_loc):
    get_raw_data(file_loc)
    try:
        with open(file_loc, encoding="utf-8") as file:
            data = json.load(file)
        print("Data extracted successfully.")
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

def load_facts(cleaned_loc):
    conn = get_database()
    cursor = conn.cursor()
    silver_layer = get_silver_layer_data(cleaned_loc)

    # Create table
    create_table = """
    CREATE TABLE IF NOT EXISTS fact_repo_snapshot (
        snapshot_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
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
    with conn.cursor() as cur:
        for row in silver_layer:
            cur.execute("""
            SELECT repo_key FROM dim_repository WHERE repo_id = %s
            """, (row["repository_id"],))
            repo_key = cur.fetchone()["repo_key"]

            cur.execute("""
            SELECT owner_key FROM dim_owner WHERE owner_id = %s
            """, (row["owner_id"],))
            owner_key = cur.fetchone()["owner_key"]

            cur.execute("""
            SELECT language_key FROM dim_language WHERE language_name = %s
            """, (row["language"],))
            language_key = cur.fetchone()["language_key"]

            d = datetime.datetime.fromisoformat(row["snapshot_date"])
            cur.execute("""
            SELECT date_key FROM dim_date WHERE year = %s AND month = %s AND DAY = %s
            """, (d.year, d.month, d.day))
            date_key = cur.fetchone()["date_key"]

            # Load fact_repo_snapshot table
            cur.execute("""
            INSERT INTO fact_repo_snapshot (repo_key, repo_id, owner_key, language_key, date_key, stars, forks, watchers)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT(repo_key, date_key)
            DO UPDATE SET
            stars = excluded.stars,
            forks = excluded.forks,
            watchers = excluded.watchers
            """, (repo_key, row["repository_id"], owner_key, language_key, date_key, row["stars"], row["fork_count"], row["watchers_count"])
            )

    conn.commit()
    conn.close()
    

def load_dimensions(cleaned_loc):
    conn = get_database()

    cursor = conn.cursor()

    # Create Dimension tables
    dim_repo = """
    CREATE TABLE IF NOT EXISTS dim_repository (
    repo_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repo_id INTEGER UNIQUE,
    repo_name TEXT
    )
        """
    dim_language = """
    CREATE TABLE IF NOT EXISTS dim_language (
    language_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    language_name TEXT UNIQUE
    )
        """
    dim_owner = """
    CREATE TABLE IF NOT EXISTS dim_owner (
    owner_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_name TEXT,
    owner_id INTEGER UNIQUE,
    owner_type TEXT
    )
        """
    dim_date = """
    CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
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

    # Get data
    silver_data = get_silver_layer_data(cleaned_loc)

    # Insert data into tables
    with conn.cursor() as cur:
        for data in silver_data:
            # Insert language into dim_language
            cur.execute("""
            INSERT INTO dim_language (language_name)
            VALUES (%s)
            ON CONFLICT DO NOTHING
            """, (data["language"],))
            # Insert repository data into dim_repo
            cur.execute("""
            INSERT INTO dim_repository (repo_id, repo_name)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING""", (int(data["repository_id"]), data["repository_name"])
            )
            # Insert owner data into dim_owner 
            cur.execute("""
            INSERT INTO dim_owner (owner_name, owner_id, owner_type)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING""", (data["owner_name"], int(data["owner_id"]), data["owner_type"])
            )
            # Insert date data into dim_date
            d = datetime.datetime.fromisoformat(data["snapshot_date"])
            cur.execute("""
            INSERT INTO dim_date (year, month, day)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING""", (d.year, d.month, d.day)
            )

    # Commit and close sqlite
    conn.commit()
    conn.close()
        
    

if __name__ == "__main__":
    main()