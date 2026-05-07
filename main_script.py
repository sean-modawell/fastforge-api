## Intro


# --- Modules & Packages ---
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests

# --- Keys ---
load_dotenv()
database_api_key = os.getenv("notion_local_api_key")
gemini_api_key = os.getenv("gemini_local_api_key")
my_client_password = os.getenv("my_local_client_password")

# --- Configuration File ---
with open("config.json", "r") as f:
    config = json.load(f)

my_name = config["my_name"]

# --- Google OAuth 2.0 ---
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/documents"]

creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        with open("token.json", "w") as f:
            f.write(creds.to_json())

drive_service = build("drive", "v3", credentials=creds)
docs_service = build("docs", "v1", credentials=creds)

# --- Initial Setup ---
app = Flask(__name__)
now = datetime.now()
current_month = now.month
current_year = now.year

# --- Helper Functions ---

def extract_json_data(incoming_data): # Process the API call from Notion and pull the PAGE_ID
    print("Call received! Data payload: ", incoming_data)
    print("Extracting data...")
    try:
        page_id = incoming_data.get("entity").get("id")
        print("Successfully saved new page_id!")
        return page_id

    except json.JSONDecodeError:
        print("Response is not valid JSON")
        return None

def request_content(page_id): # Request page content
    url = f"https://api.notion.com/v1/pages/{page_id}/markdown"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}"
    }
    print("Requesting page contents...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("Response received! Parsing for page contents...")
        try:
            data = response.json()
            page_content = data.get("markdown")
            print("Successfully saved page contents!")
            return page_content

        except json.JSONDecodeError:
            print("Response is not valid JSON")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    pass

# I am using notion as my database. The fields are deeply embedded in the json files.
def request_fields(page_id): # Request and save additional fields
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}"
    }
    print("Sending GET request for additional fields...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("Response received! Parsing...")
        try:
            data = response.json()
            record_id = data.get("properties").get("ID").get("unique_id").get("number")
            doc_heading = data.get("properties").get("title").get("rich_text")[0].get("plain_text")
            company = data.get("properties").get("company").get("rich_text")[0].get("plain_text")
            print("Successfully saved page properties!")
            return record_id, doc_heading, company

        except json.JSONDecodeError:
            print("Response is not valid JSON")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def scrape_template(): # Pull Resume from Google Drive as string
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
    print("Sending prompt to Gemini. Please wait...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        print("Response from AI received!")
        print("Parsing response...")
        try:
            ai_data = json.loads(json.dumps(response.text))

            new_intro = ai_data.get("new_intro", "")
            keyword_list = ai_data.get("keyword_list", "")
            missing_keywords = ai_data.get("missing_keywords", "")
            skills = ai_data.get("skills", "")
            print("Successfully parsed AI response!")
            return new_intro, keyword_list, missing_keywords, skills

        except json.JSONDecodeError as json_err:
            print(f"Failed to parse AI response: {json_err}")
            print("Adjust your prompt to not include conversational text.")
            return None
    
    except Exception as err:
        print(f"AI call failed: {err}")
        return None
# Add to the send_prompt function a retry loop in case of receiving a 503 error from Gemini

def create_tailored_doc(record_id, company, doc_heading, new_intro, skills): # Create new google doc from template and save URL
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
    print(f"Tailored document created: {tailored_doc_url}")
    return tailored_doc_url

def create_payload(new_intro, keyword_list, missing_keywords, tailored_doc_url, skills): # Prepare JSON payload for Notion
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
    return payload
    pass

def send_payload(page_id, payload): # Push API call to Notion
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Notion-Version": "2026-03-11",
        "Authorization": f"Bearer {database_api_key}",
        "Content-Type": "application/json"
    }
    response = requests.patch(url, json=payload, headers=headers) # Returns an updated JSON for the page
    response.raise_for_status()
    # Notion has an avg rate limit of 3 incoming requests per second 
    return response.json()
    pass


# --- Main Webhook ---
@app.route('/api/v1/doc/forge', methods=['POST'])
def forge_doc():
    provided_key = request.headers.get('Authorization')
    if provided_key != f"Bearer {my_client_password}":
        return jsonify({"status": "error", "message": "Unauthorized request"}), 401

    incoming_data = request.json
    if not incoming_data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    result = extract_json_data(incoming_data)
    if result is None:
        return jsonify({"status": "error", "message": "Failed to parse data"}), 400
    page_id = result

    result = request_content(page_id)
    if result is None:
        return jsonify({"status": "error", "message": "Could not locate page_id"}), 400
    page_content = result

    result = request_fields(page_id)
    if result is None:
        return jsonify({"status": "error", "message": "Could not pull additional fields"}), 400
    record_id, doc_heading, company = result

    result = scrape_template()
    if result is None:
        return jsonify({"status": "error", "message": "Failed to pull template"}), 400
    template_text = result

    result = create_prompt(page_content, template_text, prompt_file="prompt.txt")
    if result is None:
        return jsonify({"status": "error", "message": "Failed to create prompt"}), 400
    prompt = result

    result = send_prompt(prompt)
    if result is None:
        return jsonify({"status": "error", "message": "AI call failed"}), 400
    new_intro, keyword_list, missing_keywords, skills = result # These values will be sent to Notion
    
    result = create_tailored_doc(record_id, company, doc_heading, new_intro, skills)
    if result is None:
        return jsonify({"status": "error", "message": "Failed to create tailored document"}), 400
    tailored_doc_url = result

    payload = create_payload(new_intro, keyword_list, missing_keywords, tailored_doc_url, skills)
    send_payload(page_id, payload)

    return jsonify({"status": "success", "message": "POST request processed successfully"}), 200

if __name__ == '__main__':
    print("Starting local server on port 5000...")
    app.run(port=5000)