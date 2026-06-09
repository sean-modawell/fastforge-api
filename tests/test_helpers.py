'''
Main test suite for core functions
Testing functionality and edge cases
'''


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
from core.helpers import extract_json_data, scrape_template, create_prompt, send_prompt, create_tailored_doc, create_payload
from core.config import get_credentials, get_drive_service, get_docs_service

creds = get_credentials()
drive_service = get_drive_service(creds)
docs_service = get_docs_service(creds)

# --- extract_json_data ---
def test_extract_json_data_success(): # The id we want is entity-id. It is NOT data-parent-id. Below is the actual schema from my notion.
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

def test_extract_json_data_missing_page_id():
    test_payload = {
        "entity": {
            "type": "page"
        },
    }
    page_id = extract_json_data(test_payload)
    assert page_id is None

# def test_extract_json_data_invalid_json():

# --- create_prompt ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_PROMPT_PATH = os.path.join(BASE_DIR, "mock_prompt.txt")

def test_create_prompt_full():
    test_content = "practice content"
    test_template_text = "practice template text"
    return_prompt = create_prompt(test_content, test_template_text, prompt_file=TEST_PROMPT_PATH)
    assert return_prompt == "Content: practice content Template: practice template text"

def test_create_prompt_missing_fields():
    test_content = "practice content"
    test_template_text =  ""
    return_prompt = create_prompt(test_content, test_template_text, prompt_file=TEST_PROMPT_PATH)
    assert return_prompt == "Content: practice content Template: "

# --- create_tailored_resume ---
def test_create_tailored_doc_mock_success():
        mock_drive = MagicMock()
        mock_docs = MagicMock()
        mock_drive.files().copy().execute.return_value = {"id": "fake_doc_id_123"}
        result = create_tailored_doc(
            drive_service=mock_drive,
            docs_service=mock_docs,
            record_id="R2D2",
            company="NOMA",
            doc_heading="Software Engineer",
            new_intro="The greatest intro of all time",
            skills="Python | Automation"
        )
        assert result == "https://docs.google.com/document/d/fake_doc_id_123"
        assert mock_drive.files().copy().execute.called
        assert mock_docs.documents().batchUpdate().execute.called

# def test_create_tailored_doc_exception():

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_create_tailored_doc_real():
    result = create_tailored_doc(
        drive_service=drive_service,
        docs_service=docs_service,
        record_id="R2D2",
        company="NOMA",
        doc_heading="Software Engineer",
        new_intro="The greatest intro of all time",
        skills="Python | Automation"
    )
    assert result is not None
    assert result.startswith("https://docs.google.com/document/d/")



# --- scrape_template ---
def test_scrape_template_mock_success():
    mock_drive = MagicMock()
    mock_drive.files().export().execute.return_value = "testing".encode("utf-8")
    result = scrape_template(mock_drive)
    assert result == "testing"
    assert mock_drive.files().export().execute.called

# def test_scrape_template_mock_exception():
    result = "TODO"
    #assert result is None

# def test_scrape_template_invalid_str():
    result = "TODO"
    #assert result is None

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_scrape_template_real():
    result = scrape_template(drive_service)
    assert result is not None



# --- create_payload ---
def test_create_payload_success():
    result = create_payload(
        new_intro="Hello world",
        keyword_list="one | two | three",
        missing_keywords="four | five | six",
        tailored_doc_url="www.example.com",
        skills="seven | eight | nine"
    )
    assert result is not None
    assert result["properties"]["intro_paragraph"]["rich_text"][0]["text"]["content"] == "Hello world"
    assert result["properties"]["keyword_list"]["rich_text"][0]["text"]["content"] == "one | two | three"
    assert result["properties"]["missing_keywords"]["rich_text"][0]["text"]["content"] == "four | five | six"
    assert result["properties"]["tailored_doc_url"]["url"] == "www.example.com"
    assert result["properties"]["skills"]["rich_text"][0]["text"]["content"] == "seven | eight | nine"

# def test_create_payload_missing_field():


# --- send_prompt ---
def test_send_prompt_mock_success():
    mock_ai_response = {
        "new_intro": "The greatest intro of all time.",
        "keyword_list": ["Python", "Flask"],
        "missing_keywords": ["GitHub"],
        "skills": "Python | Flask | REST APIs"
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_ai_response)
    with patch("core.helpers.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = mock_response
        result = send_prompt("test prompt")
    assert result is not None
    new_intro, keyword_list, missing_keywords, skills = result
    assert new_intro == "The greatest intro of all time."
    assert "Python" in keyword_list
    assert "GitHub" in missing_keywords
    assert skills == "Python | Flask | REST APIs"

# def test_send_prompt_mock_exception():
    # assert result is None

# def test_send_prompt_invalid_json():
    # assert result is None

@pytest.mark.skip(reason="Real API call - run manually only") # Has passed
def test_send_prompt_real():
    mock_prompt = (
        "Respond ONLY with a valid JSON object containing exactly these keys: "
        "new_intro (string), keyword_list (array of strings), "
        "missing_keywords (array of strings), skills (string). "
        "Use placeholder values."
    )
    result = send_prompt(mock_prompt)
    assert result is not None
    new_intro, keyword_list, missing_keywords, skills = result
    assert isinstance(new_intro, str)
    assert isinstance(keyword_list, list)
    assert isinstance(skills, str)