# --- Modules & Packages ---
import os
import json
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

# --- Keys ---
load_dotenv("/etc/secrets/.env") # Path for Render
load_dotenv("setup/.env") # Local Path

database_api_key = os.environ.get("notion_local_api_key")
notion_verification_token = os.environ.get("notion_verification_token")
gemini_api_key = os.environ.get("gemini_local_api_key")
my_client_password = os.environ.get("my_local_client_password")

# --- Configuration File ---
with open("setup/config.json", "r") as f:
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