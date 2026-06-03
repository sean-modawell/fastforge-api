# Changelog

Documented iteration changes


---

## [v1.1] Async Release - 2026-06-13

- Revamped repo architecture to lessen clutter
    - Files and folders renamed
    - Helper functions 
- The main script now has a **sync** and **async** version
    - Flask and Requests library replaced by FastAPI and HTTPX
- Greater exception handling
    - Retry loop added for the following exceptions:
        - Timeouts
        - Connection errors
        - 5xx HTTP errors
    - 4xx errors
        - Note that 429 errors (Too Many Requests) will not be included in the retry loop at this time



---

## [v1.0] Initial Release - 2026-05-13

- Fully functioning for personal use