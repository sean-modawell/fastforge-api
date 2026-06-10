# --- Modules ---
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import json
import requests
from fastapi.testclient import TestClient
import httpx2

# --- Define path ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import functions from script ---
from core.helpers import extract_json_data
from main_async import app, request_content, request_fields, send_payload  # FastAPI client

def test_helpers_imported_from_async():
    result = extract_json_data({"entity": {"id": "abc123"}})
    assert result == "abc123"

def test_async_client():
    client = TestClient(app)
    response = client.post("/api/v1/doc/forge", json={})
    assert response.status_code == 401
    # 401 means the client exists and auth ran
    # 404 would mean client is offline


# --- request_content ---
test_page_id = "3123e484e34b8019bd4de26a14d50d72"

async def test_request_content_mock_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {"markdown": "# Software\n\nTitle section..."}
    with patch("httpx2.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await request_content(test_page_id)
    assert result == "# Software\n\nTitle section..."

async def test_request_content_mock_request_exception():
    with patch("httpx2.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=httpx2.RequestError("timeout"))
        result = await request_content(test_page_id)
    assert result is None

async def test_request_content_mock_invalid_json():
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
    with patch("httpx2.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await request_content(test_page_id)
    assert result is None

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
async def test_request_content_real():
    result = await request_content(test_page_id)
    assert result is not None
    assert isinstance(result, str)



# --- request_fields ---
with open("tests/api-response.json", "r") as f:
    mock_fields_payload = json.load(f)

async def test_request_fields_mock_success():
    mock_response = MagicMock()
    mock_response.json.return_value = mock_fields_payload
    with patch("httpx2.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await request_fields(test_page_id)
    assert result == (1, "Project Manager", "Acme")

async def test_request_fields_mock_request_exception():
    with patch("httpx2.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=httpx2.RequestError("timeout"))
        result = await request_fields(test_page_id)
    assert result is None

async def test_request_fields_mock_invalid_json():
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
    with patch("httpx2.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        result = await request_fields(test_page_id)
    assert result is None

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
async def test_request_fields_real():
    result = await request_fields(test_page_id)
    assert result is not None
    record_id, doc_heading, company = result
    assert isinstance(record_id, int)
    assert isinstance(doc_heading, str)
    assert isinstance(company, str)


# --- send_payload ---
async def test_send_payload_mock_success():
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
    mock_response.json.return_value = {
        "object": "page",
        "id": "mock",
        "properties":{}
    }
    with patch("httpx2.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)
        result = await send_payload(page_id="mock", payload=mock_payload)
    assert result == mock_response.json.return_value
    assert result["id"] == "mock"

# async def test_send_payload_mock_exception():
    result = "TODO"
    #assert result is None

# async def test_send_payload_mock_invalid_json():
    result = "TODO"
    #assert result is None

# @pytest.mark.skip(reason="Real API call - run manually only")
# async def test_send_payload_real():