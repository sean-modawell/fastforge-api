# FastForge API

An internal automation engine that generates context-aware documents to reduce client Time-to-Value, eliminate manual reporting errors, and scale operations without adding headcount.

---

**Project Status**: This is a fully operational internal tool developed as a reference architecture for automating documentation workflows using Flask/FastAPI and LLM integrations. While primarily a portfolio piece and for personal utility, the architecture is designed with B2B integration principles in mind, and can be adapted to internal tools and workflows. 

**Current Version**: v1.1

---

## Table of Contents

- [Overview](#overview)
- [Use Cases](#use-cases)
- [Current Features](#current-features)
- [Product Roadmap](#product-roadmap)
- [Limitations & Future Scope](#limitations--future-scope)
- [Technical Architecture](#technical-architecture)
    - [Tools Used](#tools-used)
    - [How it Works]()
    - [File Reference](#file-reference)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Questions & Contact](#questions--contact)
- [Further Reading](#further-reading)

---

## Overview

FastForge works as follows:
1. Determine Trigger
    - Workflow is triggered by an "event". This could be a new client added in your CRM, an updated status, a scheduled QBR, new prospect, really anything. 
2. Gather context
    - FastForge fetches all content related to the workflow from your database (additional sources may be connected as well)
3. Pass to GenAI
    - A prompt is sent to AI for deep analysis, complete with instructions, requirements, templates, and context.
4. Process Response
    - The response is processed and saved.
5. Forge documentation
    - The AI's recommendations are injected into a template to forge a new document.
6. Update database and stakeholders
    - Your records are updated with a link to the new document, the AI response for reference, and any additional information you would like.
    - Notifications can be sent to stakeholders for review.

[Back to Top](#table-of-contents)

---

## Use Cases & Business Solutions

FastForge can simultaneously reduce bottlenecks across various departments

| Department | Use Case | Details |
| --- | --- | --- |
| **HR & Management** | Talent Development Dossiers | Sidesteps the negative "PIP" vibe. It automatically compiles scattered performance metrics, peer feedback, and KPIs into actionable growth plans, reducing managerial bias and prep time. |
| **Customer Success** | Lifecycle Artifact Automation | Generating dynamic Quarterly Business Review (QBR) decks, personalized implementation playbooks, and automated health-check summaries. |
| **Engineering** | Stakeholder-Ready RCAs | Instantly formatting highly technical incident data into standardized Root Cause Analysis (RCA) documents that non-technical account managers can actually hand to clients. |
| **Project Management** | Automated Statements of Work (SOWs) | Moving beyond just creating tasks to generating the actual project briefs, scope documents, and integration timelines based on initial client requirements. |
| **Executive / Board** | Unified Executive Briefs | Pulling high-level metrics across departments into a single, digestible packet before major strategy meetings. |
| **Sales & RevOps** | Custom Pitch Decks & Proposals | Pulling prospect data from a CRM to automatically generate highly tailored proposal PDFs, pricing matrices, or ROI business cases for the sales team. |
| **Compliance & Legal** | Audit Trails | Automatically generating compliance reports or filling out tedious vendor security questionnaires based on a centralized database of standard company answers. |
| **FinTech / Billing** | Custom Reconciliation Reports | Beyond standard audits, generating customized end-of-month billing breakdowns for enterprise clients who require specific data formatting before they pay their invoices. |


Due to the custom API and async cababilities, multiple endpoints can be created to handle as many workflows as you like!


In my personal workflow, I update the record to "Review". There, I can look over the work, make any adjustments as needed, and then execute it.

Components:
Database "Source of Truth" - CRM(Salesforce, HubSpot), ERP, HCM/HRIS, or SQL based - I use Notion
Server - Where the script lives. Can be local or Cloud - I use Render
Framework - FastAPI or Flask - Flask for small scale
Cloud DocHub - Google Drive, OneDrive, Sharepoint, Dropbox - I use Google Drive
AI/LLM - ChatGPT, Gemini, Claude, Internal - I use Google Gemini Flash model

[Back to Top](#table-of-contents)

---

## Current Features

[Back to Top](#table-of-contents)

---

## Product Roadmap

Upcoming features:
1. Support for per second and per minute rate limits
    - Support will not be added for daily rate limits in this feature, though support for multiple accounts is being considered for later
2. Support for additional databases
3. Support for additianal server providers (not just render)

[Back to Top](#table-of-contents)

---

## Limitations & Future Scope

The output of your workflow is mainly limited by AI capability. These limitations can mostly be overcome by the following:

- Prompt Design:
The quality of your prompt determines your final output. Vague or incomplete prompts lead to unhelpful output, which defeats the purpose of this automation. Much can be acheived by AI today with the proper prompt.

- Custom AI/LLM:
Creating your own AI model, utilizing machine learning to train it on your own internal data, giving it read access to your database/knowledgebase, will get you the best output. Doing so is easier than ever. [Hugging Face](https://huggingface.co/) has a wealth of base models at your disposal, completely free. Find the one that best fits your use case, download it, connect it to your internal data (read-access-only), and start training.


### What’s Configurable (Without Touching Code)

**You can adjust:**

- The prompt sent to Gemini
- **Sync** vs **Async** workflow


**Currently not configurable:**

- AI provider (locked to Google Gemini)
- Total number of fields processed
- The number of output fields
- Document storage (locked to Google Drive)
- Document format (Google Docs only — not `.docx`)



[Back to Top](#table-of-contents)

---

## Technical Architecture

### Tools Used

|Component                 |Tool                         |Why                                     |
|--------------------------|-----------------------------|----------------------------------------|
|Database (Source of Truth)|Notion                       |Free API, great for project management  |
|Browser Clipping          |Save to Notion (extension)   |Easy way to add jobs to the workflow    |
|Doc Storage               |Google Drive / Google Docs   |Free API, dynamic, and easy to update   |
|GenAI Model               |Google Gemini (Flash)        |Free API tier; ChatGPT no longer has one|
|Server hosting            |[Render](https://render.com/)|Free tier for personal apps             |
|Web framework             |Flask / FastAPI              |Lightweight and supports local hosting  |

### How it Works

1. Create a new page in Notion. Using the **Save to Notion** browser extension
2. Notion sends a webhook to this microservice, FastForge API
3. The app pulls the context data, fetches your base template from Google Drive, and sends everything to **Google Gemini**
4. Gemini returns structured suggestions for tailoring your template document
5. The results are saved to a new **Google Doc** for your review before proceeding

The app is built with **Flask** and can be hosted locally or on a free [Render](https://render.com/) instance.

### File Reference

#### `.env`

- Stores your secret keys. **Never commit this file to version control.**
- Create a `.env` file in the root folder using the `.env.example`


#### `prompt.txt`

- The prompt sent to Gemini. The entire contents of this file are read and submitted as-is — no comments are supported.
- Use `{{double_curly_braces}}` for dynamic tags that get replaced at runtime. For example:
    - Here is my content: {{page_content}}
    - Here is my template: {{template_text}}


#### `config.json`

Configuration that doesn’t belong in `.env`. This is where you adjust things like Notion database field names or the number of fields you want to process — without needing to touch the Python code.

[Back to Top](#table-of-contents)

---

## Getting Started

### Prerequisites

[Back to Top](#table-of-contents)

### Installation

Clone the repo and set up a virtual environment:

```bash
    git clone https://github.com/Sean-DM2022/fastforge-api.git
    cd fastforge-api
    python -m venv .venv
    source .venv/bin/activate  # Windows: source .venv/Scripts/activate
    pip install -r requirements.txt
```

[Back to Top](#table-of-contents)

### Configuration

#### Get your API keys

- **Notion**: Go to [notion.so/my-integrations](https://www.notion.so/my-integrations), create a new integration, and copy the secret key. Make sure your integration has access to the database you’re using.
- **Gemini**: Go to [aistudio.google.com](https://aistudio.google.com) and generate an API key.
- **Google Drive / Docs**: Set up a OAuth 2.0 Client in the [Google Cloud Console](https://console.cloud.google.com/), enable the Drive and Docs APIs, and download the credentials JSON.
- **Client password**: Choose any password. This is used to authenticate requests to your Flask server.

See below for notes on OAuth vs Service_account

#### Configure your `.env`

Copy the template above into a new `.env` file in the root folder and fill in your keys.

#### Set up your template in Google Drive (WIP)

Store your **base_template** as a Google Doc. The script fetches it fresh on each run, so any updates you make to the doc are automatically picked up.

For customizing, it’s recommended to maintain a second Google Doc as a **tagged_template**, a copy of your base template with sections replaced by `{{TAGS}}`. Gemini’s suggestions can then be slotted directly into the template.

#### Write your prompt

Edit `prompt.txt` with the instructions you want to send to Gemini. Use `{{tags}}` to reference dynamic values, like the specific context or your output template. The quality of AI output depends heavily on prompt quality — see the note below.

#### Configure `config.json` (WIP)

Adjust field names and settings to match your Notion database setup.

[Back to Top](#table-of-contents)

---

## Usage & API Examples

[Back to Top](#table-of-contents)

---

## Contributing

While this is primarily a personal portfolio project, feedback, issue reports, and pull requests are always welcome.

[Back to Top](#table-of-contents)

---

## License

>Pending

[Back to Top](#table-of-contents)

---

## Questions & Contact

Feel free to open an issue or reach out via GitHub.
You may also reach out to me over [LinkedIn](https://www.linkedin.com/in/sean-modawell/).

[Back to Top](#table-of-contents)

---

## Further Reading

### Hosting

#### Locally (Flask)

Flask’s built-in server lets you run the app on your machine. Useful for testing or if you’re always on the same computer.


#### On Render (recommended for portability)

[Render](https://render.com/) offers a free tier that works well for small-scale or personal apps. Connect your GitHub repo and it will deploy automatically on each push.

> **Note:** Free Render instances go dormant after 15 minutes of inactivity. Expect a 30–60 second delay on the first webhook while the instance wakes up.

-----

### Prompt Design

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

### Google Services: OAuth vs service_account

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

### Notion API Notes

[API Reference](https://developers.notion.com/reference/intro)

#### rich_text objects

For those of you unfamiliar with rich_text objects, the entire paragraph is a LIST of dictionaries. This is to support multiple formats within the same string. Where a new format begins, a new block/dictionary is added to the list.

```json
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

### Notes on my Process

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
