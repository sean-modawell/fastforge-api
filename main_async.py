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

# --- Logging Settings ---
logging.basicConfig(level=logging.DEBUG) # DEBUG > INFO > WARNING > ERROR > CRITICAL
logger = logging.getLogger(__name__)

# --- Keys ---
load_dotenv("/etc/secrets/.env") # Path for Render
load_dotenv() # Local Path
logging.info(f"Refresh token loaded: {bool(os.environ.get('GOOGLE_REFRESH_TOKEN'))}") # Most common point of failure. This makes sure the OAuth workflow functions

database_api_key = os.environ.get("notion_local_api_key")
notion_verification_token = os.environ.get("notion_verification_token")
gemini_api_key = os.environ.get("gemini_local_api_key")
my_client_password = os.environ.get("my_local_client_password")

# --- Configuration File ---
with open("config.json", "r") as f:
    config = json.load(f)

my_name = config["my_name"]

# --- Google OAuth 2.0 ---
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/documents"]

def get_credentials():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds

def get_drive_service(creds):
    drive_service = build("drive", "v3", credentials=creds)
    return drive_service

def get_docs_service(creds):
    docs_service = build("docs", "v1", credentials=creds)
    return docs_service

# --- Initial Setup ---
app = FastAPI()
now = datetime.now()
current_month = now.month
current_year = now.year

# --- Helper Functions ---
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

def extract_json_data(incoming_data): # Process the API call from Notion and pull the PAGE_ID
    logger.debug("Extracting data...")
    try:
        page_id = incoming_data.get("entity").get("id")
        logger.debug("Successfully saved new page_id!")
        return page_id

    except json.JSONDecodeError:
        logger.error("Response is not valid JSON")
        return None

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


def scrape_template(drive_service): # Pull Resume from Google Drive as string
    template_id = config["base_template_id"]
    template_text = drive_service.files().export(
        fileId=template_id,
        mimeType="text/plain" # returns as bytes and not a string
    ).execute().decode("utf-8") # Google export() does not auto-decode/convert "text/plain". We need to convert it to a string with .decode()
    return template_text

def create_prompt(page_content, template_text, prompt_file="prompt.txt"): # Call prompt.txt, insert current template TEXT and doc_content TEXT
    with open(prompt_file, "r") as f:
        prompt = f.read()
    prompt = prompt.replace("{{page_content}}", page_content)
    prompt = prompt.replace("{{template_text}}", template_text)
    return prompt
# Add a try/exception to make sure the page_content and template_text are not blank.

def send_prompt(prompt): # Send & Receive
    client = genai.Client(api_key=gemini_api_key)
    logger.info("Sending prompt to Gemini. Please wait...")
    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        logger.info("Response from AI received! Parsing...")
        try:
            ai_data = json.loads(response.text)

            new_intro = ai_data.get("new_intro", "")
            keyword_list = ai_data.get("keyword_list", "")
            missing_keywords = ai_data.get("missing_keywords", "")
            skills = ai_data.get("skills", "")
            logger.info("Successfully parsed AI response!")
            return new_intro, keyword_list, missing_keywords, skills

        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse AI response: {json_err}")
            logger.error("Adjust your prompt to not include conversational text.")
            return None
    
    except Exception as err:
        logger.error(f"AI call failed: {err}")
        return None
# Add to the send_prompt function a retry loop in case of receiving a 503 error from Gemini

def create_tailored_doc(drive_service, docs_service, record_id, company, doc_heading, new_intro, skills): # Create new google doc from template and save URL
    # Copy the template Doc
    template_id = config["tagged_template_id"]
    response = drive_service.files().copy( # command to copy a google doc
        fileId=template_id, # selects the proper file
        body={
            "name": f"ID-{record_id} - {company} ({current_month}/{current_year})",
            "parents": [config["output_folder"]]
        },
        supportsAllDrives=True
    ).execute()
    new_doc_id = response["id"]

    # Replace {{tags}}
    docs_service.documents().batchUpdate(
        documentId=new_doc_id,
        body={"requests": [
            {"replaceAllText": {"containsText": {"text": "{{doc_heading}}"}, "replaceText": doc_heading}},
            {"replaceAllText": {"containsText": {"text": "{{introduction_paragraph}}"}, "replaceText": new_intro}},
            {"replaceAllText": {"containsText": {"text": "{{skills}}"}, "replaceText": skills}},
        ]}
    ).execute()

    # Return URL
    tailored_doc_url = f"https://docs.google.com/document/d/{new_doc_id}"
    logger.info(f"Tailored document created: {tailored_doc_url}")
    return tailored_doc_url

def create_payload(new_intro, keyword_list, missing_keywords, tailored_doc_url, skills): # Prepare JSON payload for Notion
    logger.debug("Constructing payload...")
    payload = {
        "properties": {
            "status": {
                "status": { "name": "review_doc" },
            },
            "intro_paragraph": { "rich_text": [{ "text": { "content": f"{new_intro}" } }] },
            "keyword_list": { "rich_text": [{ "text": { "content": f"{keyword_list}" } }] },
            "missing_keywords": { "rich_text": [{ "text": { "content": f"{missing_keywords}" } }] },
            "tailored_doc_url": { "url": f"{tailored_doc_url}" },
            "skills": { "rich_text": [{ "text": { "content": f"{skills}" } }] },
        },
    }
    logger.debug("Payload created")
    return payload

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
    """
    # Notion first sends a verification code. This block of code is to capture it in the Render Log so we can save it
    data = request.get_json()
    print("Incoming payload:", data)  # this shows up in Render logs
    return jsonify({"status": "ok"}), 200
    # It is recommended to comment out the rest of the function 
    """

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