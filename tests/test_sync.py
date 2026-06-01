

from core.helpers import extract_json_data, create_payload
from main_sync import app  # Flask app & client

def test_helpers_imported_from_sync():
    result = extract_json_data({"entity": {"id": "abc123"}})
    assert result == "abc123"

def test_sync_client():
    import flask.testing
    client = app.test_client()
    response = client.post("/api/v1/doc/forge", json={})
    assert response.status_code == 401
    # 401 means the client exists and auth ran
    # 404 would mean client is offline