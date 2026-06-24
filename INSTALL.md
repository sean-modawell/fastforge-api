# FastForge — Installation & Configuration Guide
 
This guide is written for developers setting up FastForge for their own workflow. It assumes familiarity with Python, REST APIs, and basic cloud console navigation.

---

## Table of Contents
 
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
  - [API Keys](#api-keys)
  - [Google Cloud & OAuth Setup](#google-cloud--oauth-setup)
  - [Environment Variables](#environment-variables)
  - [config.json](#configjson)
- [Document Template Setup](#document-template-setup)
- [Prompt Engineering](#prompt-engineering)
- [Notion Webhook Setup](#notion-webhook-setup)
- [Deployment](#deployment)
- [Testing](#testing)
- [Helpful Links](#helpful-links)
- [Additional Notes](#additional-notes)
   - [rich_text objects](#rich_text-objects)

---

## Prerequisites
 
- Python 3.10+
- Git
- Notion workspace with API access
- Google account (personal is fine — see [OAuth notes](#google-cloud--oauth-setup))
- IDE of your choice

---

## Installation
 
```bash
git clone https://github.com/sean-modawell/fastforge-api.git
cd fastforge-api
python -m venv .venv
source .venv/bin/activate  # Windows: source .venv/Scripts/activate
pip install -r requirements.txt
```
 
---

## Project Structure (Simplified)

```
fastforge-api/
├── core/
│   ├── config.py
│   └── helpers.py
├── setup/
│   ├── config.json
│   ├── credentials.json
│   ├── examples/
│   │   ├── config.example.json
│   │   ├── credentials.example.json
│   │   ├── prompt.example.txt
│   │   └── test_request.http
│   ├── generate_token.py
│   ├── notion_sandbox.py
│   ├── prompt.txt
│   └── token.json
└── tests
│   ├── mock_prompt.txt
│   ├── test_async.py
│   ├── test_helpers.py
│   └── test_sync.py
├── initial.py
├── main_async.py
├── main_sync.py
├── render.yaml
└── requirements.txt
```

---
 
## Configuration
 
### API Keys
 
You will need credentials from three services before running the app.
 
**Notion**
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) and create a new integration
2. Enter a name and select an Authentication method: we will use `Access token`
2. Copy and save the Integration access token
3. Select **Content Access** tab → **Edit Access** → Search your database name → click and **Save**

**Gemini**
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Generate an API key and copy it

**Google Cloud**
Follow the [Google Cloud & OAuth Setup](#google-cloud--oauth-setup) section below — there are more steps involved.
 
---
 
### Google Cloud & OAuth Setup
 
> **OAuth 2.0 vs. Service Account**
>
> A service account is cleaner to maintain long-term (no token rotation), but on a free/personal Google account, the service account cannot be the *owner* of newly created Drive files — which means it cannot create new Google Docs. If you are running this under a **Google Workspace business account**, you can configure the service account with the necessary Drive permissions, and it is the preferred approach.
>
> For personal accounts, **OAuth 2.0** is the correct path and is what these steps cover.
 
1. Open the [Google Cloud Console](https://console.cloud.google.com/) and create a new project
2. In the left nav, go to **APIs & Services → Library**, select and enable both:
   - Google Drive API
   - Google Docs API
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth Client ID**
4. Choose your application type → enter a Name → click **Create**:
   - **Desktop App** — recommended for local development and testing
   - **Web Application** — for Render deployment; a URI is not necessary
5. Download the credentials JSON and save it to `/setup` as `credentials.json`
   - This filename is already in `.gitignore`
   - Add GOOGLE_CLIENT_SECRET & GOOGLE_CLIENT_ID to you `.env`
6. Go to **APIs & Services → OAuth Consent Screen**
   - Navigate to **Audience**
   - **User type** should be set to **External**
   - Under **Test Users**, add the Google account you will authenticate with
7. Generate your refresh token by running the token script locally:
```bash
   python setup/generate_token.py
```
   - A browser window will open for OAuth sign-in
   - If the window does not open automatically, the link will appear in your terminal. Copy the URL
   - If you have multiple Google accounts logged in, copy the URL into an incognito window to avoid account confusion
   - After signing in, the redirect page may show an error — this is expected. Click **Try Again**
   - A `token.json` file will be written to `/setup`. This file is in `.gitignore`
8. Copy the `refresh_token` value from `token.json` and save it as `GOOGLE_REFRESH_TOKEN` in your `.env`
> **Token expiry:** While your OAuth app is in Testing mode, Google expires all refresh tokens after 7 days — including for test users. To remove this limit, either publish the OAuth app (goes through Google verification) or migrate to a service account under a Google Workspace account. See the [README](README.md#supported-integrations) for roadmap context.
 
---
 
### Environment Variables
 
Copy `setup/examples/.env.example` to `.env` in the project root and fill in all values:
 
```env
NOTION_SECRET=ntn_...
NOTION_DATABASE_ID=...
NOTION_VERIFICATION_TOKEN=secret_...
 
GEMINI_API_KEY=...
 
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```
 
> The app uses `os.environ[]` (not `.get()`) for all required credentials. Missing values raise a `KeyError` at startup — intentionally loud so failures surface immediately rather than mid-request.
 
---
 
### config.json
 
Copy `setup/examples/config.json.example` to `setup/config.json`.
 
This file holds the Google Doc IDs for your base and tagged templates. To find a document ID, open it in Google Docs — the ID is the string between `/d/` and `/edit` in the URL:
 
```
https://docs.google.com/document/d/1dizHrezuyheme2ewSEGolSw5C4zKcn0Ky23KgO7u-p2M/edit
                                    └──────────────── Document ID ────────────┘
```
 
---
 
## Document Template Setup
 
FastForge uses two Google Docs templates per workflow.
 
**Base Template**
Your reference document — a completed example of what the output should look like. This is passed to Gemini alongside the prompt so it can match structure, tone, and formatting. Start with an existing document or build one from scratch.
 
**Tagged Template**
A duplicate of the base template where each AI-generated section is replaced with a `{{tag}}` placeholder. At runtime, the app replaces each tag with the corresponding key from Gemini's JSON response.
 
Steps:
1. Create or identify your base template document in Google Docs
2. Duplicate it
3. In the duplicate, replace each AI-generated section with a `{{tag}}` — keys must match exactly what your prompt instructs Gemini to return in its JSON
4. Add both document IDs to `setup/config.json`
---
 
## Prompt Engineering
 
The prompt is the highest-leverage variable in the system. A well-crafted prompt produces output that requires no edits. A vague prompt produces output that creates more work than it saves.
 
A production-ready prompt should include:
- Clear instructions on what Gemini should generate for each section
- Full workflow context and the specific use case
- Your base template as a formatting and tone reference
- An explicit JSON output template instruction, with keys that match your `{{tags}}`

Here are two articles that discuss prompt engineering in greater detail:
[Google](https://cloud.google.com/discover/what-is-prompt-engineering)
[MIT Sloan](https://mitsloanedtech.mit.edu/ai/basics/effective-prompts/)

**Recommended iteration workflow:**
1. Draft your prompt in `setup/prompt.txt`
2. Test it directly on [gemini.google.com](https://gemini.google.com) — Model = 3.1 Flash-Lite — avoid burning API tokens during iteration
3. Adjust until the output requires no (or minimal) manual edits
4. The finalized prompt is what gets sent via the API at runtime
> Prompt iteration takes time. Expect multiple rounds before it feels right. Small, targeted adjustments tend to have the greatest impact on output quality.
 
---

## Notion Webhook Setup
 
Notion requires a publicly accessible endpoint to verify ownership before it will deliver webhook events. The `initial.py` script is a minimal server designed specifically for this handshake — it does nothing else.
 
1. Deploy a server running `initial.py` on Render or any publicly accessible host
```bash
gunicorn initial:app --timeout 120
```
2. In Notion, open your integration settings and create a new webhook subscription:
   - **Event type:** `page_created`
   - **Endpoint URL:** your public server URL
3. Click **Verify** — Notion will POST a verification token to your endpoint
4. Check your server logs for the verification_token
5. Save the token to `NOTION_VERIFICATION_TOKEN` in your `.env`
Reference: [Notion Webhooks API](https://developers.notion.com/reference/webhooks)
 
---
 
## Deployment
 
### Local
 
For development and testing, Flask's built-in server is sufficient:
 
```bash
# Sync (Flask)
python main_sync.py
 
# Async (FastAPI)
uvicorn main_async:app --reload
```
 
### Render (Recommended for Portability)
 
1. Connect your GitHub repo to [Render](https://render.com/) — it will deploy automatically on each push
2. Add all `.env` values as environment variables in the Render dashboard
3. Mount `credentials.json` as a secret file at `/etc/secrets/credentials.json`
   - The app resolves credential paths using `os.path.exists()` branching to handle both Render (`/etc/secrets/`) and local paths
4. Set the **Start Command** based on your preferred workflow:
   **Sync (Flask + Gunicorn):**
```bash
   gunicorn main_sync:app --timeout 120
```
 
   **Async (FastAPI + Uvicorn worker):**
```bash
   gunicorn -k uvicorn.workers.UvicornWorker main_async:app --timeout 120
```
 
   > The `--timeout 120` flag is important — Gunicorn's default 30-second worker timeout will kill long-running Gemini API calls before they complete. Adjust as needed based on your average generation time.
 
> **Free tier note:** Render free instances go dormant after 15 minutes of inactivity. Expect a 30–60 second cold-start delay on the first webhook after dormancy. This does not affect paid tiers.
 
---
 
## Testing
 
```bash
pytest -s
```
 
The `-s` flag captures `logging` output alongside test results, which is useful for tracing external API call behavior during development.
 
**Test file responsibilities:**
 
| File | Purpose |
|---|---|
| `test_helpers.py` | Core business logic — primary suite |
| `test_sync.py` | Flask route wiring & **Sync**-specific logic |
| `test_async.py` | FastAPI route wiring & **Async**-specific logic |
 
External dependencies (Gemini, Google Drive, Notion) are mocked using `unittest.mock`. Async tests use `AsyncMock` and `anyio`.

---

## Helpful Links

[Notion API Reference](https://developers.notion.com/reference/intro)
[Render](https://render.com/)
[Gemini](https://gemini.google.com)
[Google Cloud Console](https://console.cloud.google.com/)
[My Notion Integrations](https://www.notion.so/my-integrations)
[API Key for Gemini](https://aistudio.google.com)

---

## Additional Notes

### Notion

#### `rich_text` objects

For those of you unfamiliar with rich_text objects, the entire paragraph is an unindexed LIST of dictionaries. This is to support multiple formats within the same string. Where a new format begins, a new block/dictionary is added to the list.

See the `request_fields()` function from `main_sync.py`/`main_async.py`. This is where it comes into play.

```json
"rich_text": [
    {
        "type": "text",
        "text": {
            "content": "block 0",
            "link": null
        },
        "annotations": {
            "bold": false,
            "italic": false,
            "strikethrough": false,
            "underline": false,
            "code": false,
            "color": "default"
        },
        "plain_text": "example",
        "href": null
    }
]
[
    {
        "type": "text",
        "text": {
            "content": "block 1",
            "link": null
        },
        "annotations": {
            "bold": true,
            "italic": false,
            "strikethrough": false,
            "underline": false,
            "code": false,
            "color": "default"
        },
        "plain_text": "example",
        "href": null
    }
] 
```

`plain_text` is READ-ONLY. It is to provide "a convenient way for developers to access unformatted text from the Notion block"
This is the property you will want to access when using a GET request

In order to POST/PUT text, you will need to write to the `text.content` property. Any additional formatting is optional.