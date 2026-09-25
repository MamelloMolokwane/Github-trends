import pandas as pd
from scripts import load
from unittest.mock import MagicMock


def test_get_silver_layer_data(tmp_path):
    file_path = tmp_path / "silver.csv"

    expected = pd.DataFrame({
        "repository_id": [1, 2],
        "repository_name": ["repo-one", "repo-two"],
        "language": ["Python", "Java"]
    })
    expected.to_csv(file_path, index=False)
    result = load.get_silver_layer_data(str(file_path))

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result["repository_name"]) == [
        "repo-one",
        "repo-two"
    ]

def test_load_dimensions(monkeypatch):
    df = pd.DataFrame({
        "repository_id": [1],
        "repository_name": ["test-repository"],
        "language": ["Python"],
        "owner_name": ["test-user"],
        "owner_id": [100],
        "owner_type": ["User"],
        "snapshot_date": ["2026-09-25T00:00:00"]
    })

    fake_connection = MagicMock()
    fake_cursor = MagicMock()

    fake_connection.cursor.return_value = fake_cursor
    fake_cursor.__enter__.return_value = fake_cursor

    monkeypatch.setattr(
        load,
        "get_database",
        lambda: fake_connection
    )

    load.load_dimensions(df)

    assert fake_cursor.execute.called
    assert fake_connection.commit.called
    assert fake_connection.close.called

def test_load_facts():
    df = pd.DataFrame({
        "repository_id": [1],
        "language": ["Python"],
        "owner_id": [100],
        "snapshot_date": ["2026-09-25T00:00:00"],
        "stars": [500],
        "fork_count": [50],
        "watchers_count": [25]
    })

    fake_connection = MagicMock()
    fake_cursor = MagicMock()

    fake_connection.cursor.return_value = fake_cursor

    fake_cursor.__enter__.return_value = fake_cursor
    fake_cursor.__exit__.return_value = None

    # Responses from the four SELECT queries
    fake_cursor.fetchone.side_effect = [
        {"repo_key": 1},
        {"owner_key": 2},
        {"language_key": 3},
        {"date_key": 4}
    ]

    original_get_database = load.get_database
    load.get_database = lambda: fake_connection

    try:
        load.load_facts(df)

        assert fake_cursor.execute.called
        assert fake_connection.commit.called
        assert fake_connection.close.called

    finally:
        load.get_database = original_get_database