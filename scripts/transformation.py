import pandas as pd
import datetime
import requests
import psycopg
import json
import os


def transform(raw_loc, cleaned_loc):
    """ Transform and clean the data then save it in the silver layer """

    with open(raw_loc, encoding="utf-8") as file:
        raw_data = json.load(file)

    df = pd.json_normalize(raw_data["items"])

    df = df.rename(columns={
        "id": "repository_id",
        "name": "repository_name",
        "html_url": "repository_link",
        "owner.id": "owner_id",
        "owner.login": "owner_name",
        "owner.type": "owner_type",
        "stargazers_count": "stars",
        "forks_count": "fork_count"
    })

    df["topics"] = df["topics"].apply(json.dumps)
    df = df.drop_duplicates()
    # filter to only keep the coloumns needed
    df = df[
        [
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
            "open_issues_count",
            "archived",
            "fork",
            "topics"
        ]
    ]

    df["snapshot_date"] = datetime.date.today().isoformat()
    df["language"] = df["language"].fillna("Unknown")
    df["description"] = df["description"].fillna("")
    df["repository_name"] = df["repository_name"].str.strip()
    df["repository_link"] = df["repository_link"].str.strip()
    df["owner_name"] = df["owner_name"].str.strip()
    df["owner_type"] = df["owner_type"].str.strip()
    df["language"] = df["language"].str.strip()
    df["description"] = df["description"].str.strip()

    # Save in csv file
    os.makedirs(os.path.dirname(cleaned_loc), exist_ok=True)
    df.to_csv(cleaned_loc, index=False)

    print("Data has been transformed and put into the silver the layer.")
    return df