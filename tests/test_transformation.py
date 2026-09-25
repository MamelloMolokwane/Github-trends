import json
import pandas as pd
from scripts.transformation import transform


def test_transform_creates_csv(tmp_path):
    raw_file = tmp_path / "raw.json"
    cleaned_file = tmp_path / "cleaned.csv"
    fake_data = {
        "items": [
            {
                "id": 123,
                "name": " test-repo ",
                "html_url": " https://github.com/test/test-repo ",
                "owner": {
                    "id": 456,
                    "login": " test-user ",
                    "type": " User "
                },
                "description": None,
                "stargazers_count": 100,
                "forks_count": 20,
                "language": None,
                "created_at": "2026-09-09T10:00:00Z",
                "updated_at": "2026-09-09T11:00:00Z",
                "watchers_count": 50,
                "open_issues_count": 5,
                "archived": False,
                "fork": False,
                "topics": ["python", "data"]
            }
        ]
    }

    with open(raw_file, "w", encoding="utf-8") as file:
        json.dump(fake_data, file)
    transform(str(raw_file), str(cleaned_file))

    assert cleaned_file.exists()

def test_transform_cleans_data(tmp_path):
    raw_file = tmp_path / "raw.json"
    cleaned_file = tmp_path / "cleaned.csv"
    fake_data = {
        "items": [
            {
                "id": 123,
                "name": " test-repo ",
                "html_url": " https://github.com/test/test-repo ",
                "owner": {
                    "id": 456,
                    "login": " test-user ",
                    "type": " User "
                },
                "description": None,
                "stargazers_count": 100,
                "forks_count": 20,
                "language": None,
                "created_at": "2026-09-09T10:00:00Z",
                "updated_at": "2026-09-09T11:00:00Z",
                "watchers_count": 50,
                "open_issues_count": 5,
                "archived": False,
                "fork": False,
                "topics": ["python", "data"]
            }
        ]
    }

    with open(raw_file, "w", encoding="utf-8") as file:
        json.dump(fake_data, file)

    transform(str(raw_file), str(cleaned_file))
    df = pd.read_csv(cleaned_file)

    assert df.iloc[0]["repository_name"] == "test-repo"
    assert df.iloc[0]["repository_link"] == "https://github.com/test/test-repo"
    assert df.iloc[0]["owner_name"] == "test-user"
    assert df.iloc[0]["owner_type"] == "User"
    assert df.iloc[0]["language"] == "Unknown"
    assert pd.isna(df.iloc[0]["description"])

def test_transform_has_expected_columns(tmp_path):
    raw_file = tmp_path / "raw.json"
    cleaned_file = tmp_path / "cleaned.csv"
    fake_data = {
        "items": [
            {
                "id": 123,
                "name": "test-repo",
                "html_url": "https://github.com/test/test-repo",
                "owner": {
                    "id": 456,
                    "login": "test-user",
                    "type": "User"
                },
                "description": "Test repository",
                "stargazers_count": 100,
                "forks_count": 20,
                "language": "Python",
                "created_at": "2026-09-09T10:00:00Z",
                "updated_at": "2026-09-09T11:00:00Z",
                "watchers_count": 50,
                "open_issues_count": 5,
                "archived": False,
                "fork": False,
                "topics": []
            }
        ]
    }

    with open(raw_file, "w", encoding="utf-8") as file:
        json.dump(fake_data, file)

    transform(str(raw_file), str(cleaned_file))
    df = pd.read_csv(cleaned_file)

    expected_columns = [
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
        "topics",
        "snapshot_date"
    ]

    assert list(df.columns) == expected_columns