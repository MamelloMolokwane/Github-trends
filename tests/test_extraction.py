import json
from scripts import extraction


def test_get_raw_data_creates_json_file(tmp_path, monkeypatch):
    file_path = tmp_path / "raw.json"

    class FakeResponse:
        status_code = 200
        def json(self):
            return {
                "items": [
                    {
                        "id": 123,
                        "name": "test-repository"
                    }
                ]
            }

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(extraction.requests, "get", fake_get)

    extraction.get_raw_data(str(file_path))

    assert file_path.exists()

    with open(file_path) as file:
        data = json.load(file)

    assert data["items"][0]["id"] == 123
    assert data["items"][0]["name"] == "test-repository"


def test_get_raw_data_does_not_create_file_when_request_fails(
    tmp_path,
    monkeypatch,
    capsys
):
    file_path = tmp_path / "raw.json"

    class FakeResponse:
        status_code = 500
        text = "Internal Server Error"

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(extraction.requests, "get", fake_get)

    extraction.get_raw_data(str(file_path))

    assert not file_path.exists()

    captured = capsys.readouterr()

    assert "500" in captured.out

def test_extract_returns_error_when_file_does_not_exist(tmp_path, monkeypatch):
    file_path = tmp_path / "missing.json"

    def fake_get_raw_data(file_loc):
        pass

    monkeypatch.setattr(
        extraction,
        "get_raw_data",
        fake_get_raw_data
    )

    result = extraction.extract(str(file_path))

    assert result == f"{file_path} not found"