## Intro
'''
This script does the following:
- Creates Flask instance
- Defines syncronous specific functions
- Defines complete workflow
- Receives webhook at API endpoint
    - Responds to client with success or failure message
    - Starts workflow as a new thread
'''

# --- Modules & Packages ---
from flask import Flask, request, jsonify
import os
import json
import requests
import hmac
import hashlib
import threading


# --- Helper Functions ---
from core.helpers import extract_json_data, scrape_template, create_prompt, send_prompt, create_tailored_doc, create_payload
from core.config import get_credentials, get_drive_service, get_docs_service, database_api_key, notion_verification_token, logger

# --- Initial Setup ---
app = Flask(__name__)

# --- Helper Functions ---
def verify_notion_signature(request):
    logger.info("Verifying signature...")
    try:
        weave = request.headers.get('X-Notion-Signature')
        body = request.get_data()
    except json.JSONDecodeError:
        logger.error("Post request is not valid JSON")
        return None

    if not weave:  # header missing entirely
        logger.warning("X-Notion-Signature header missing")
        return False

    yarn = 'sha256=' + hmac.new(
        notion_verification_token.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(weave, yarn)

def request_content(page_id): # Request page content
    url = f"https://api.notion.com/v1/pages/{page_id}/markdown"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}"
    }
    logger.debug("Requesting page contents...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.debug(f"Notion [{response.status_code}]: {response.text}")
        response.raise_for_status()
        logger.info("Response received! Parsing for page contents...")
        try:
            data = response.json()
            page_content = data.get("markdown")
            logger.info("Successfully saved page contents!")
            return page_content

        except json.JSONDecodeError:
            logger.error("Response is not valid JSON")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error: {e}")
        return None

# I am using notion as my database. The fields are deeply embedded in the json files.
def request_fields(page_id): # Request and save additional fields
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}"
    }
    logger.info("Sending GET request for additional fields...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.debug(f"Notion GET Request [{response.status_code}]: {response.text}")
        response.raise_for_status()
        logger.info("Response received! Parsing...")
        try:
            data = response.json()
            record_id = data.get("properties").get("ID").get("unique_id").get("number")
            doc_heading = data.get("properties").get("title").get("rich_text")[0].get("plain_text")
            company = data.get("properties").get("company").get("rich_text")[0].get("plain_text")
            logger.info("Successfully saved page properties!")
            return record_id, doc_heading, company

        except json.JSONDecodeError:
            logger.error("Response is not valid JSON")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None


    # Return URL
    tailored_doc_url = f"https://docs.google.com/document/d/{new_doc_id}"
    logger.info(f"Tailored document created: {tailored_doc_url}")
    return tailored_doc_url


def send_payload(page_id, payload): # Push API call to Notion
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}",
        "Content-Type": "application/json"
    }
    logger.info("Sending PATCH request")
    response = requests.patch(url, json=payload, headers=headers) # Returns an updated JSON for the page
    logger.debug(f"Notion PATCH Request [{response.status_code}]: {response.text}")
    response.raise_for_status()
    # Notion has an avg rate limit of 3 incoming requests per second
    return response.json()


# --- Main Webhook ---
def forge_doc(payload):
    creds = get_credentials()
    drive_service = get_drive_service(creds)
    docs_service = get_docs_service(creds)

    result = extract_json_data(payload)
    if result is None:
        return
    page_id = result

    result = request_content(page_id)
    if result is None:
        return
    page_content = result

    result = request_fields(page_id)
    if result is None:
        return
    record_id, doc_heading, company = result

    result = scrape_template(drive_service)
    if result is None:
        return
    template_text = result

    result = create_prompt(page_content, template_text)
    if result is None:
        return
    prompt = result

    result = send_prompt(prompt)
    if result is None:
        return
    new_intro, term_analysis, gap_analysis, highlights = result # These values will be sent to Notion
    
    result = create_tailored_doc(drive_service, docs_service, record_id, company, doc_heading, new_intro, highlights)
    if result is None:
        return
    tailored_doc_url = result

    payload = create_payload(new_intro, term_analysis, gap_analysis, tailored_doc_url, highlights)
    send_payload(page_id, payload)
    logger.info("Successfully sent PATCH request")
    logger.info("Workflow complete")


@app.route('/api/v1/doc/forge', methods=['POST'])
def receive_webhook():
    if not verify_notion_signature(request):
        logger.error("Error: Invalid signature")
        return jsonify({"status": "error", "message": "Unauthorized request"}), 401
    logger.debug("Signature verified")

    payload = request.get_json()
    if not payload:
        logger.error("Error: No data provided")
        return jsonify({"status": "error", "message": "No data provided"}), 400

    thread = threading.Thread(target=forge_doc, args=(payload,))
    thread.daemon = True
    thread.start()
    logger.debug("Starting thread...")
    logger.debug("Sending response to client...")
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    print("Starting local server on port 5000...")
    app.run(port=5000)