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
from main_script import extract_json_data
from main_script import request_content
from main_script import request_fields
from main_script import create_prompt
from main_script import send_prompt 
from main_script import create_tailored_doc
from main_script import scrape_template



# --- extract_json_data ---
def test_extract_json_data_full(): # The id we want is entity-id. It is NOT data-parent-id. Below is the actual schema from my notion.
    test_payload = {
        "id": "88888c",
        "timestamp": "2026-04-27T23:27:54.876Z",
        "workspace_id": "adf3e484",
        "workspace_name": "Notion Workspace",
        "subscription_id": "34fd872b",
        "integration_id": "312d872b",
        "authors": [
            {
            "id": "1f9d872b",
            "type": "person"
            }
        ],
        "attempt_number": 1,
        "api_version": "2026-03-11",
        "entity": {
            "id": "abc123",
            "type": "page"
        },
        "type": "page.created",
        "data": {
            "parent": {
                "id": "3123e484668",
                "type": "database",
                "data_source_id": "3123e484dci"
            }
        }
    }
    page_id = extract_json_data(test_payload)
    assert page_id == "abc123"

def test_extract_json_data_missing_fields():
    test_payload = {
        "entity": {
            "type": "page"
        },
    }
    page_id = extract_json_data(test_payload)
    assert page_id is None



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

@pytest.mark.skip(reason="Real API call - run manually only")
def test_request_content_real():
    result = request_content(test_page_id)
    assert result is not None
    assert isinstance(result, str)



# --- request_fields ---
mock_fields_payload = "Hello"

def test_request_fields_mock_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = mock_fields_payload
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = request_fields(test_page_id)
    mock_get.assert_called_once()
    assert result == (7, "Software Engineer Resume", "Acme Corp")

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

@pytest.mark.skip(reason="Real API call - run manually only")
def test_request_fields_real():
    result = request_fields(test_page_id)
    assert result is not None
    record_id, doc_heading, company = result
    assert isinstance(record_id, int)
    assert isinstance(doc_heading, str)
    assert isinstance(company, str)



# --- create_prompt ---
def test_create_prompt_full():
    test_content = "practice content"
    test_template_text = "practice template text"
    return_prompt = create_prompt(test_content, test_template_text, prompt_file="tests/test_prompt.txt")
    assert return_prompt == "Content: practice content Template: practice template text"

def test_create_prompt_missing_fields():
    test_content = "practice content"
    test_template_text =  ""
    return_prompt = create_prompt(test_content, test_template_text, prompt_file="tests/test_prompt.txt")
    assert return_prompt == "Content: practice content Template: "



# --- send_prompt ---
def test_send_prompt_mock_api():
    mock_ai_response = {
        "new_intro": "The greatest intro of all time.",
        "keyword_list": ["Python", "Flask"],
        "missing_keywords": ["GitHub"],
        "skills": "Python | Flask | REST APIs"
    }
    mock_response = MagicMock()
    mock_response.text = mock_ai_response
    with patch("main_script.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = mock_response
        result = send_prompt("test prompt")
    assert result is not None
    new_intro, keyword_list, missing_keywords, skills = result
    assert new_intro == "The greatest intro of all time."
    assert "Python" in keyword_list
    assert "GitHub" in missing_keywords
    assert skills == "Python | Flask | REST APIs"

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_send_prompt_real():
    test_prompt = (
        "Respond ONLY with a valid JSON object containing exactly these keys: "
        "new_intro (string), keyword_list (array of strings), "
        "missing_keywords (array of strings), skills (string). "
        "Use placeholder values."
    )
    result = send_prompt(test_prompt)
    assert result is not None
    new_intro, keyword_list, missing_keywords, skills = result
    assert isinstance(new_intro, str)
    assert isinstance(keyword_list, list)
    assert isinstance(skills, str)



# --- create_tailored_resume ---
def test_create_tailored_doc_mock():
    with (patch("main_script.drive_service") as mock_drive, patch("main_script.docs_service") as mock_docs):
        mock_drive.files().copy().execute.return_value = {"id": "fake_doc_id_123"}
        result = create_tailored_doc(
            record_id="R2D2",
            company="NOMA",
            doc_heading="Software Engineer",
            new_intro="The greatest intro of all time",
            skills="Python | Automation"
        )
        assert result == "https://docs.google.com/document/d/fake_doc_id_123"
        assert mock_drive.files().copy().execute.called
        assert mock_docs.documents().batchUpdate().execute.called

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_create_tailored_doc_real():
    result = create_tailored_doc(
        record_id="R2D2",
        company="NOMA",
        doc_heading="Software Engineer",
        new_intro="The greatest intro of all time",
        skills="Python | Automation"
    )
    assert result is not None
    assert result.startswith("https://docs.google.com/document/d/")



# --- scrape_template ---
def test_scrape_template_mock():
    with (patch("main_script.drive_service") as mock_drive):
        mock_bytes = "testing".encode("utf-8")
        mock_drive.files().export().execute.return_value = mock_bytes
        result = scrape_template()
        assert result == "testing"
        assert mock_drive.files().export().execute.called

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_scrape_template_real():
    result = scrape_template()

    assert result is not None