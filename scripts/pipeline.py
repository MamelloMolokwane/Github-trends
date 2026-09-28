from load import load_facts, load_dimensions
from transformation import transform
from database import get_database
from extraction import extract
import datetime


def main():
    bronze_layer = f"./data/bronze/raw_repo_{datetime.date.today().isoformat()}.json"
    silver_layer = f"./data/silver/cleaned_repo_{datetime.date.today()}.csv"
    
    extract(bronze_layer)
    print("Finished with extraction moving on to transformation...")

    # Transform the data then return it
    df = transform(bronze_layer, silver_layer)
    print("Finished with transformation moving on loading dimension...")
    # Create dimensions
    load_dimensions(df)
    print("Finished loading dimensions, moving on too loading facts...")
    # Create fact table
    load_facts(df)
    print("Finished loading facts. Pipeline loaded.")

    table_check()
    print("Warehouse created.")

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
    

if __name__ == "__main__":
    main()