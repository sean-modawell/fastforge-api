## Intro

# --- Modules & Packages ---
from core.config import get_credentials, get_drive_service, get_docs_service, gemini_api_key
import logging
from datetime import datetime
import json
from google import genai
from google.genai import types
import os

# --- Logging Settings ---
logging.basicConfig(level=logging.DEBUG) # DEBUG > INFO > WARNING > ERROR > CRITICAL
logger = logging.getLogger(__name__)

# --- Current Date ---
now = datetime.now()
current_month = now.month
current_year = now.year

# --- Absolute Directory Path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "..", "setup", "config.json")
PROMPT_PATH = os.path.join(BASE_DIR, "..", "setup", "prompt.txt")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# --- Helper Functions ---
def extract_json_data(incoming_data): # Process the API call from Notion and pull the PAGE_ID
    logger.debug("Extracting data...")
    try:
        page_id = incoming_data.get("entity").get("id")
        logger.debug("Successfully saved new page_id!")
        return page_id

    except json.JSONDecodeError:
        logger.error("Response is not valid JSON")
        return None

def scrape_template(drive_service): # Pull Resume from Google Drive as string
    template_id = config["base_template_id"]
    template_text = drive_service.files().export(
        fileId=template_id,
        mimeType="text/plain" # returns as bytes and not a string
    ).execute().decode("utf-8") # Google export() does not auto-decode/convert "text/plain". We need to convert it to a string with .decode()
    return template_text

def create_prompt(page_content, template_text, prompt_file=PROMPT_PATH): # Call prompt.txt, insert current template TEXT and doc_content TEXT
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
            "name": f"ID-{record_id} - {company} ({current_month}-{current_year})",
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