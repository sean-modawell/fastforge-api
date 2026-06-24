## Intro
'''
This script handles the following:
- Logging Configuration
- Loading Environment Variables
- Google OAuth 2.0 Workflow
'''


# --- Modules & Packages ---
import os
import json
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import logging

# --- Logging Settings ---
logging.basicConfig(level=logging.DEBUG) # DEBUG > INFO > WARNING > ERROR > CRITICAL
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
load_dotenv("/etc/secrets/.env") # Path for Render
load_dotenv("setup/.env") # Local Path

database_api_key = os.environ["notion_local_api_key"]
notion_verification_token = os.environ["notion_verification_token"]
gemini_api_key = os.environ["gemini_local_api_key"]

# --- Google OAuth 2.0 ---
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/documents"]

def get_credentials():
    logging.debug("refresh_token: %s", bool(os.environ.get("GOOGLE_REFRESH_TOKEN")))
    logging.debug("client_id: %s", bool(os.environ.get("GOOGLE_CLIENT_ID")))
    logging.debug("client_secret: %s", bool(os.environ.get("GOOGLE_CLIENT_SECRET")))
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(GoogleRequest())
    return creds

def get_drive_service(creds):
    drive_service = build("drive", "v3", credentials=creds)
    return drive_service

def get_docs_service(creds):
    docs_service = build("docs", "v1", credentials=creds)
    return docs_service