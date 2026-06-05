
from core.helpers import extract_json_data
from main_async import app  # FastAPI client
from fastapi.testclient import TestClient

def test_helpers_imported_from_async():
    result = extract_json_data({"entity": {"id": "abc123"}})
    assert result == "abc123"

def test_async_client():
    client = TestClient(app)
    response = client.post("/api/v1/doc/forge", json={})
    assert response.status_code == 401
    # 401 means the client exists and auth ran
    # 404 would mean client is offline