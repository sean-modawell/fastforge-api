# FastForge API

A Python-based microservice utilizing LLM, webhooks, and databases to dynamically create context-aware documents.

-----

## WORK IN PROGRESS

This project is still in development. I work on it in my freetime. There are 9 helper functions to the main webhook.

Current Status: 9 of 9 helper functions are tested and functional. Greater error handling to come.

> **Note:** I remove `pass` from a function once it is complete and has passed pytest.

-----

## Overview

Use Cases
1. Custom Onboarding Guides/Runbooks
2. Financial Audit Briefs
3. Incident Post-Mortems
4. Dynamic SLA's


The workflow:

1. Create a new page in Notion. Using the **Save to Notion** browser extension
2. Notion sends a webhook to this microservice, FastForge API
3. The app pulls the context data, fetches your base template from Google Drive, and sends everything to **Google Gemini**
4. Gemini returns structured suggestions for tailoring your template document
5. The results are saved to a new **Google Doc** for your review before proceeding

The app is built with **Flask** and can be hosted locally or on a free [Render](https://render.com/) instance.

-----

## Tools Used

|Purpose             |Tool                      |Why                                     |
|--------------------|--------------------------|----------------------------------------|
|Database            |Notion                    |Free API, great for project management  |
|Browser clipping    |Save to Notion (extension)|Easy way to add jobs to the workflow    |
|Doc storage         |Google Drive / Google Docs|Free API, dynamic and easy to update    |
|AI suggestions      |Google Gemini (Flash)     |Free API tier; ChatGPT no longer has one|
|Server hosting      |Render                    |Free tier for personal apps             |
|Web framework       |Flask                     |Lightweight; supports local hosting too |

-----

## File Reference

### `.env`

Stores your secret keys. **Never commit this file to version control.**

Create a `.env` file in the root folder using the `.env.example`


### `prompt.txt`

The prompt sent to Gemini. The entire contents of this file are read and submitted as-is — no comments are supported.

Use `{{double_curly_braces}}` for dynamic tags that get replaced at runtime. For example:


Here is my content: {{page_content}}
Here is my template: {{template_text}}


### `config.json`

Configuration that doesn’t belong in `.env`. This is where you adjust things like Notion database field names or the number of fields you want to process — without needing to touch the Python code.

-----

## Setup Instructions

### 1. Initial Installation

Clone the repo and set up a virtual environment:

    git clone https://github.com/Sean-DM2022/fastforge-api.git
    cd fastforge-api
    python -m venv .venv
    source .venv/bin/activate  # Windows: source .venv/Scripts/activate
    pip install -r requirements.txt

Then continue with the setup steps below.

### 2. Get your API keys

- **Notion**: Go to [notion.so/my-integrations](https://www.notion.so/my-integrations), create a new integration, and copy the secret key. Make sure your integration has access to the database you’re using.
- **Gemini**: Go to [aistudio.google.com](https://aistudio.google.com) and generate an API key.
- **Google Drive / Docs**: Set up a OAuth 2.0 Client in the [Google Cloud Console](https://console.cloud.google.com/), enable the Drive and Docs APIs, and download the credentials JSON.
- **Client password**: Choose any password. This is used to authenticate requests to your Flask server.

See below for notes on OAuth vs Service_account

### 3. Configure your `.env`

Copy the template above into a new `.env` file in the root folder and fill in your keys.

### 4. Set up your template in Google Drive (WIP)

Store your **base_template** as a Google Doc. The script fetches it fresh on each run, so any updates you make to the doc are automatically picked up.

For customizing, it’s recommended to maintain a second Google Doc as a **tagged_template**, a copy of your base template with sections replaced by `{{TAGS}}`. Gemini’s suggestions can then be slotted directly into the template.

### 5. Write your prompt

Edit `prompt.txt` with the instructions you want to send to Gemini. Use `{{tags}}` to reference dynamic values, like the specific context or your output template. The quality of AI output depends heavily on prompt quality — see the note below.

### 6. Configure `config.json` (WIP)

Adjust field names and settings to match your Notion database setup.

-----

## Hosting

### Locally (Flask)

Flask’s built-in server lets you run the app on your machine. Useful for testing or if you’re always on the same computer.


### On Render (recommended for portability)

[Render](https://render.com/) offers a free tier that works well for small-scale or personal apps. Connect your GitHub repo and it will deploy automatically on each push.

> **Note:** Free Render instances go dormant after 15 minutes of inactivity. Expect a 30–60 second delay on the first webhook while the instance wakes up.

-----

## A Note on Prompt Design

The quality of Gemini’s suggestions depends entirely on the quality of your prompt. Vague or incomplete prompts lead to unhelpful output, which defeats the purpose of this automation.

A good prompt typically includes:

- Clear instructions on what you want (e.g., “suggest edits to the bullet points under Experience”)
- The full context and use case
- Your base template/output
- The format you want the response in (the app expects structured JSON)

Treat your `prompt.txt` as something worth iterating on. Small improvements to the prompt can have a big impact on the output.

It is also worth testing your prompt directly on the [Gemini App](https://gemini.google.com/). This avoids wasting API tokens and allows you to easily adjust the prompt.

I have worked through many iterations of my prompt to get it just right for me. This part takes time and experimentation.

-----

## Google Services: OAuth vs service_account

I started off attempting to use a service_account for my workflow. I ran into the issue that, on a free tier, the service_account is unable to create new google docs and files. Simply put, your service_account cannot be the 'owner' of the file. If you are running this within a business account, you can make adjustments to give the service_account permissions to create files.

If you do not have a business account or paid account, have no fear. This can be completed by using an OAuth Client ID. I will walk you through the steps for this, as there is a lot.
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project
3. With the project selected, open the left navigation menu
4. Select APIs & Services > Credentials
5. Select Create credentials > OAuth client ID
6. Two Options
    A. For Application type:
        1. Web application
            a. Give it a name
            b. Add URIs
            c. Click Create
        2. Desktop App
            a. Give it a name
            b. Click Create
    ** I suggest starting with a Desktop App while testing, then switching to the Web Application when you are ready for deployment.
7. Save json for credentials
8. Place json in root folder and save as "credentials.json"
    ** File name is already added to .gitignore
7. Select Audience
8. Add Test User email and save
9. Run pytest and follow the pop up to sign in
    ** If you have multiple google accounts on the same browser, it may not go through. Copy the URL into an incognito window. After signing in, it initially fails. This is okay. Select 'Try Again'.
    ** This process generates a token to the root folder so you won't have to sign in each time. This file will be named "token.json" automatically and the filename is already added to the .gitignore
10. All set!
    
-----
## What’s Configurable (Without Touching Code)

**You can adjust:**

- Notion database field names (WIP)
- Total number of fields processed (WIP)
- The prompt sent to Gemini
- The number of output fields (WIP)

**Currently not configurable:**

- AI provider (locked to Google Gemini)
- Document storage (locked to Google Drive)
- Document format (Google Docs only — not `.docx`)

-----

## Notion API Notes

[API Reference](https://developers.notion.com/reference/intro)

rich_text objects

rich_text is a LIST of dictionaries. This is to support multiple formats. Where a new format begins, a new block/dictionary is added to the list.

```
"rich_text": [
    {
        "type": "text",
        "text": {
            "content": "example",
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
```
Some very important notes:
plain_text is READ-ONLY. It is to provide "a convenient way for developers to access unformatted text from the Notion block"
This is the property you will want to access when using a GET request

In order to POST text, you will need to write to the text.content property. Any additional formatting is optional.


-----

## Questions?

Feel free to open an issue or reach out via GitHub. Contributions and suggestions are welcome.

-----

## Notes on my Process

This is a personal project to replace a MS Power Automate flow I created.

The Steps to my project:
1. Map the Process
2. Write the framework for main webhook
3. Create all stub functions
4. Map the functions within the webhook
5. Code a function and its dependencies
6. Test/Debug the function
7. Repeat steps 5 & 6 until script complete
8. Complete Notion API setup
9. Host script locally for end-to-end testing/debugging
10. Deploy application on Render
