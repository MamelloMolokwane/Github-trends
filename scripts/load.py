import pandas as pd
import datetime
from database import get_database


# Create function to get repos
def get_silver_layer_data(silver_layer):   
    return pd.read_csv(silver_layer)

def load_facts(df):
    conn = get_database()
    cursor = conn.cursor()

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
        for row in df.itertuples(index=False):
            cur.execute("""
            SELECT repo_key FROM dim_repository WHERE repo_id = %s
            """, (row.repository_id,))
            repo_key = cur.fetchone()["repo_key"]

            cur.execute("""
            SELECT owner_key FROM dim_owner WHERE owner_id = %s
            """, (row.owner_id,))
            owner_key = cur.fetchone()["owner_key"]

            cur.execute("""
            SELECT language_key FROM dim_language WHERE language_name = %s
            """, (row.language,))
            language_key = cur.fetchone()["language_key"]

            d = datetime.datetime.fromisoformat(row.snapshot_date)
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
            """, (repo_key, row.repository_id, owner_key, language_key, date_key, row.stars, row.fork_count, row.watchers_count)
            )

    conn.commit()
    conn.close()
    

def load_dimensions(df):
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

    # Insert data into tables
    with conn.cursor() as cur:
        for data in df.itertuples(index=False):
            # Insert language into dim_language
            cur.execute("""
            INSERT INTO dim_language (language_name)
            VALUES (%s)
            ON CONFLICT DO NOTHING
            """, (data.language,))
            # Insert repository data into dim_repo
            cur.execute("""
            INSERT INTO dim_repository (repo_id, repo_name)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING""", (int(data.repository_id), data.repository_name)
            )
            # Insert owner data into dim_owner 
            cur.execute("""
            INSERT INTO dim_owner (owner_name, owner_id, owner_type)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING""", (data.owner_name, int(data.owner_id), data.owner_type)
            )
            # Insert date data into dim_date
            d = datetime.datetime.fromisoformat(data.snapshot_date)
            cur.execute("""
            INSERT INTO dim_date (year, month, day)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING""", (d.year, d.month, d.day)
            )

    # Commit and close sqlite
    conn.commit()
    conn.close()