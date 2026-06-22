from datetime import date, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import requests
import sqlite3
import json
import csv
import os

TOKEN = "MY_TOKEN"

def main():
    bronze_layer = f"./data/bronze/raw_repo_{date.today().isoformat()}.json"
    silver_layer = f"./data/silver/cleaned_repo_{date.today()}.csv"
    # gold_layer = f"./data/bronze/raw_repo_{date.today()}.json"
    data = extract(bronze_layer)
    print("Finished with extraction moving on to transformation...")
    transform(bronze_layer, silver_layer)
    print("Finished with transformation moving on load...")
    
    

def get_raw_data(file_loc):
    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "Application/vnd.github+json"
    }
    # Get repositories from the last 3 months
    last_3_months = (date.today() - timedelta(days=90)).isoformat()
    params = {
        "q": f"created:>{last_3_months}",
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

    with open(raw_loc, encoding="utf-8") as file:
        raw_data = json.load(file)

    for data in raw_data["items"]:
        clean = {
            "repository_id": data["id"],
            "repository_name": data["name"],
            "repository_link": data["html_url"],
            "owner_id": data["owner"]["id"],
            "owner_name": data["owner"]["login"],
            "owner_type": data["owner"]["type"],
            "description": data["description"],
            "stars": data["stargazers_count"],
            "fork_count": data["forks_count"],
            "language": data["language"] or "Uknown",
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "watchers_count": data["watchers_count"],
            "snapshot_date": date.today().isoformat(),
            "open_issues_count": data["open_issues_count"],
            "archived": data["archived"],
            "fork": data["fork"],
            "topics": data["topics"]
        }
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

    return "Data has been transformed and put into the silver the layer."

def load():
    conn = sqlite3.connect("github-trends.db")
    # Store the data in a database.
    ...

if __name__ == "__main__":
    main()