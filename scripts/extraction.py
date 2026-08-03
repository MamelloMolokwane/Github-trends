from dotenv import load_dotenv
import datetime
import requests
import json
import os

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")


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