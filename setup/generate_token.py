# For LOCAL USE ONLY

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/documents"]

flow = InstalledAppFlow.from_client_secrets_file("setup/credentials.json", SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

with open("setup/token.json", "w") as f:
    f.write(creds.to_json())

print("Done!")

'''
Run this command in the root directory: `python setup/generate_token.py`
The link may not open automatically in your browser:
    1. Copy the link (in VSCode, ctrl+click then select copy)
    2. Open a private browser **
    3. Sign in to the account associated with your `credentials.json` file
    4. Window: Google hasn't verified this app
        - click `Continue`
    5. Make sure to give access to all services
    6. This message will appear in your browser once done
        `The authentication flow has completed. You may close this window.`

**If I am signed into multiple google accounts in my browser, the OAuth2.0 process has issues
'''