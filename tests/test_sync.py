# --- Modules ---
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import json
import requests

# --- Define path ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import functions from script ---
from core.helpers import extract_json_data
from main_sync import app, request_content, request_fields, send_payload  # Flask app & client

def test_helpers_imported_from_sync():
    result = extract_json_data({"entity": {"id": "abc123"}})
    assert result == "abc123"

def test_sync_client():
    import flask.testing
    client = app.test_client()
    response = client.post("/api/v1/doc/forge", json={})
    print(response.data)
    assert response.status_code == 401
    # 401 means the client exists and auth ran
    # 404 would mean client is offline


# --- request_content ---
test_page_id = "3123e484e34b8019bd4de26a14d50d72"

def test_request_content_mock_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()  # No-op; simulates 200 OK
    mock_response.json.return_value = {"markdown": "# Software\n\nTitle section..."}
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = request_content(test_page_id)
    mock_get.assert_called_once()
    assert result == "# Software\n\nTitle section..."

def test_request_content_mock_request_exception():
    with patch("requests.get", side_effect=requests.exceptions.RequestException("timeout")):
        result = request_content(test_page_id)
    assert result is None

def test_request_content_mock_invalid_json():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
    with patch("requests.get", return_value=mock_response):
        result = request_content(test_page_id)
    assert result is None

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_request_content_real():
    result = request_content(test_page_id)
    assert result is not None
    assert isinstance(result, str)



# --- request_fields ---
with open("tests/api-response.json", "r") as f:
    mock_fields_payload = json.load(f)

def test_request_fields_mock_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = mock_fields_payload
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = request_fields(test_page_id)
    mock_get.assert_called_once()
    assert result == (1, "Project Manager", "Acme")

def test_request_fields_mock_request_exception():
    with patch("requests.get", side_effect=requests.exceptions.RequestException("connection error")):
        result = request_fields(test_page_id)
    assert result is None

def test_request_fields_mock_invalid_json():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
    with patch("requests.get", return_value=mock_response):
        result = request_fields(test_page_id)
    assert result is None

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_request_fields_real():
    result = request_fields(test_page_id)
    assert result is not None
    record_id, doc_heading, company = result
    assert isinstance(record_id, int)
    assert isinstance(doc_heading, str)
    assert isinstance(company, str)


# --- send_payload ---
def test_send_payload_mock_success():
    mock_payload = {
        "properties": {
            "status": {
                "status": { "name": "review_doc" },
            },
            "intro_paragraph": { "rich_text": [{ "text": { "content": "new_intro" } }] },
            "term_analysis": { "rich_text": [{ "text": { "content": "term_analysis" } }] },
            "gap_analysis": { "rich_text": [{ "text": { "content": "gap_analysis" } }] },
            "tailored_doc_url": { "url": "tailored_doc_url" },
            "highlights": { "rich_text": [{ "text": { "content": "highlights" } }] },
        },
    }
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "object": "page",
        "id": "mock",
        "properties":{}
    }
    with patch("requests.patch", return_value=mock_response) as mock_patch:
        result = send_payload(page_id="mock", payload=mock_payload)
    mock_patch.assert_called_once()
    called_url = mock_patch.call_args[0][0]
    assert called_url == "https://api.notion.com/v1/pages/mock"
    mock_response.raise_for_status.assert_called_once()
    assert result == mock_response.json.return_value
    assert result["id"] == "mock"

# def test_send_payload_mock_exception():
    result = "TODO"
    #assert result is None

# def test_send_payload_mock_invalid_json():
    result = "TODO"
    #assert result is None

# @pytest.mark.skip(reason="Real API call - run manually only")
# def test_send_payload_real():