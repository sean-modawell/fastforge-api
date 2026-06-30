# FastForge API

**Automated, context-aware document generation — triggered by your workflow, built around your data.**

FastForge is a backend automation engine that connects your database, cloud storage, and AI to generate fully formatted, tailored documents in seconds.

No manual assembly, no copy-paste errors, no bottlenecks.

---

**Version**: v1.1 | **Status**: Production

---

## Table of Contents

- [FastForge API](#fastforge-api)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [How It Works](#how-it-works)
  - [Use Cases](#use-cases)
  - [Current Features](#current-features)
  - [Supported Integrations](#supported-integrations)
  - [Technical Architecture](#technical-architecture)
    - [Flow Diagram](#flow-diagram)
  - [Product Roadmap](#product-roadmap)
  - [Getting Started](#getting-started)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

---

## Overview

**Reduce Time-to-Value, eliminate errors, and scale operations without adding headcount.**

FastForge eliminates the manual effort behind routine documentation. It listens for events in your workflow, pulls the right context from your database, sends everything to an AI model with a purpose-built prompt, and outputs a finished document — formatted, consistent, and ready for review.

Documents that would take 30–60 minutes to assemble manually are generated in seconds. The output is structured, repeatable, and free of the bias and variation that comes with manual processes.

FastForge runs as a microservice and supports multiple independent workflows through separate API endpoints — meaning you can automate across departments from a single deployment.

---

## How It Works

1. **Trigger** — A workflow event fires (new client added, status updated, QBR due). FastForge receives it via webhook.
2. **Gather Context** — The app fetches all relevant data from your Notion database.
3. **AI Analysis** — A structured prompt — including instructions, context, and your base template — is sent to Google Gemini.
4. **Process Response** — Gemini's structured JSON response is parsed into discrete document sections.
5. **Forge the Document** — AI-generated content is injected into your Google Docs template, producing a complete, formatted document.
6. **Update & Notify** — The source record is updated with a link to the new document. Stakeholders can be notified for review before any external actions are taken.

---

## Use Cases

FastForge can reduce documentation bottlenecks across various departments simultaneously.

| Department | Use Case | Details |
| --- | --- | --- |
| **HR & Management** | Talent Development Dossiers | Compiles scattered performance metrics, peer feedback, and KPIs into actionable growth plans — reducing managerial bias and prep time. |
| **Customer Success** | Lifecycle Artifact Automation | Generates dynamic QBR decks, personalized implementation playbooks, and automated health-check summaries. |
| **Engineering** | Stakeholder-Ready RCAs | Formats technical incident data into standardized Root Cause Analysis documents that non-technical account managers can deliver to clients. |
| **Project Management** | Automated Statements of Work (SOWs) | Generates project briefs, scope documents, and integration timelines directly from initial client requirements. |
| **Executive / Board** | Unified Executive Briefs | Pulls high-level metrics across departments into a single digestible packet before strategy meetings. |
| **Sales & RevOps** | Custom Proposals & Pitch Decks | Pulls prospect data from a CRM to generate tailored proposals, pricing matrices, or ROI business cases. |
| **Compliance & Legal** | Audit Trails | Generates compliance reports or fills vendor security questionnaires from a centralized database of standard company answers. |
| **FinTech / Billing** | Custom Reconciliation Reports | Generates customized end-of-month billing breakdowns for enterprise clients with specific formatting requirements. |

---

## Current Features

- **Webhook Ingestion** — Receives and verifies Notion webhook events using HMAC-SHA256 signature validation
- **LLM Integration** — Sends structured prompts to Google Gemini and processes structured JSON responses into discrete document sections
- **Template Injection** — Replaces `{{tagged}}` placeholders in Google Docs templates with AI-generated content
- **Sync & Async Support** — Parallel implementations: Flask (sync, Gunicorn) and FastAPI (async, Uvicorn) — choose based on your deployment needs
- **Notion DB Integration** — Reads context data from source records and writes back document links and AI output on completion
- **Configurable Prompts** — Prompt is externalized and iterable without touching application code
- **Retry Logic** — Tenacity-based retry wrapper on all external API calls with configurable backoff
- **Structured Error Handling** — Per-call try/except blocks with logging; fails fast on missing credentials at startup rather than silently mid-request

---

## Supported Integrations

| Layer | Current Support |
|---|---|
| Database | Notion |
| Document Storage | Google Drive |
| Document Format | Google Docs |
| AI Model | Google Gemini (Flash) |
| Hosting | Render / Local |

**On the roadmap:** Additional database and document storage integrations are planned. See [Product Roadmap](#product-roadmap) for details. The API-driven architecture is designed to accommodate new integrations without structural changes.

---

## Technical Architecture

| Component | Tool | Rationale |
|---|---|---|
| Database | Notion | Free API; well-structured for project and content management |
| Document Storage | Google Drive / Docs | Free API; dynamic and programmatically updatable |
| AI Model | Google Gemini Flash | Free API tier; strong instruction-following; structured JSON output |
| Hosting | Render | Free tier suitable for personal and small-scale deployments |
| Web Framework | Flask / FastAPI | Lightweight; supports both sync and async patterns |
| Webhook Auth | HMAC-SHA256 | Secure signature verification on all incoming webhook events |
| Retry Logic | Tenacity | Configurable retry with backoff for all external API calls |

---

### Flow Diagram

```
Notion (Webhook) ──► FastForge API ──► Google Gemini
                          │                  │
                          │         Structured JSON Response
                          │                  │
                          └──► Google Docs Template Injection
                          │
                          └──► Notion DB Update (doc link + AI output)
```

---

## Product Roadmap

1. **Rate limit support** — Per-second and per-minute rate limiting for Gemini API calls *(in progress)*
2. **Additional database support** — Integrations beyond Notion (e.g., Airtable, HubSpot, custom sources)
3. **Additional hosting support** — Deployment support beyond Render
4. **Schema-based configuration** — Full workflow customization (fields, endpoints, document structure) without touching code

---

## Getting Started

See [INSTALL.md](INSTALL.md) for complete setup instructions.

**Prerequisites:** Python, Git, a Notion workspace, and a Google account.

---

## Contributing

Feedback, issue reports, and pull requests are welcome.

---

## License

MIT License — Copyright (c) 2026 Sean Modawell

---

## Contact

Open an issue on GitHub or connect via [LinkedIn](https://www.linkedin.com/in/sean-modawell/).