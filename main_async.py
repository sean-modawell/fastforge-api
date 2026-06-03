## Intro


# --- Modules & Packages ---
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import httpx
import hmac
import hashlib
import logging

# --- Helper Functions ---
from core.helpers import extract_json_data, scrape_template, create_prompt, send_prompt, create_tailored_doc, create_payload
from core.config import get_credentials, get_drive_service, get_docs_service

# --- Logging Settings ---
logging.basicConfig(level=logging.DEBUG) # DEBUG > INFO > WARNING > ERROR > CRITICAL
logger = logging.getLogger(__name__)

# --- Keys ---
load_dotenv("/etc/secrets/.env") # Path for Render
load_dotenv("setup/.env") # Local Path
logging.info(f"Refresh token loaded: {bool(os.environ.get('GOOGLE_REFRESH_TOKEN'))}") # Most common point of failure. This makes sure the OAuth workflow functions

database_api_key = os.environ.get("notion_local_api_key")
notion_verification_token = os.environ.get("notion_verification_token")
gemini_api_key = os.environ.get("gemini_local_api_key")
my_client_password = os.environ.get("my_local_client_password")

# --- Configuration File ---
with open("config.json", "r") as f:
    config = json.load(f)

my_name = config["my_name"]


# --- Initial Setup ---
app = FastAPI()
now = datetime.now()
current_month = now.month
current_year = now.year

# --- Unique Async Functions ---
async def verify_notion_signature(request):
    logger.info("Verifying signature...")
    try:
        weave = request.headers.get('X-Notion-Signature')
        body = request.get_data()
    except json.JSONDecodeError:
        logger.error("Post request is not valid JSON")
        return None

    yarn = 'sha256=' + hmac.new(
        notion_verification_token.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(weave, yarn)

async def request_content(page_id): # Request page content
    url = f"https://api.notion.com/v1/pages/{page_id}/markdown"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}"
    }
    logger.debug("Requesting page contents...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10)
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
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            return None

        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return None

# I am using notion as my database. The fields are deeply embedded in the json files.
async def request_fields(page_id): # Request and save additional fields
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}"
    }
    logger.info("Sending GET request for additional fields...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10)
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

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            return None

        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return None


async def send_payload(page_id, payload): # Push API call to Notion
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}",
        "Content-Type": "application/json"
    }
    logger.info("Sending PATCH request")
    async with httpx.AsyncClient() as client:
        response = await client.patch(url, json=payload, headers=headers) # Returns an updated JSON for the page
        logger.debug(f"Notion PATCH Request [{response.status_code}]: {response.text}")
        response.raise_for_status()
        # Notion has an avg rate limit of 3 incoming requests per second
        return response.json()


# --- Main Webhook ---
@app.route('/api/v1/doc/forge')
async def forge_doc():
    if not await verify_notion_signature(request):
        logger.error("Error: Invalid signature")
        raise HTTPException(status_code=401, detail="Unauthorized request")
    logger.debug("Signature verified")

    creds = get_credentials()
    drive_service = get_drive_service(creds)
    docs_service = get_docs_service(creds)

    incoming_data = await request.json()
    if not incoming_data:
        raise HTTPException(status_code=400, detail="No data provided")

    result = extract_json_data(incoming_data)
    if result is None:
        raise HTTPException(status_code=400, detail="Failed to parse data")
    page_id = result

    result = request_content(page_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Could not locate page_id")
    page_content = result

    result = request_fields(page_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Could not pull additional fields")
    record_id, doc_heading, company = result

    result = scrape_template(drive_service)
    if result is None:
        raise HTTPException(status_code=400, detail="Failed to pull template")
    template_text = result

    result = create_prompt(page_content, template_text, prompt_file="prompt.txt")
    if result is None:
        raise HTTPException(status_code=400, detail="Failed to create prompt")
    prompt = result

    result = send_prompt(prompt)
    if result is None:
        raise HTTPException(status_code=400, detail="AI call failed")
    new_intro, keyword_list, missing_keywords, skills = result # These values will be sent to Notion
    
    result = create_tailored_doc(drive_service, docs_service, record_id, company, doc_heading, new_intro, skills)
    if result is None:
        raise HTTPException(status_code=400, detail="Failed to create tailored document")
    tailored_doc_url = result

    payload = create_payload(new_intro, keyword_list, missing_keywords, tailored_doc_url, skills)
    send_payload(page_id, payload)
    logger.info("Successfully sent PATCH request")
    logger.info("Workflow complete")
    return JSONResponse(content={"status": "success", "message": "POST request processed successfully"}, status_code=200)