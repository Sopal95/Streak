# HTML → Website Converter

A full-stack project using **Python FastAPI** (backend) + **Vanilla JS** (frontend) + **Claude AI** to fetch any website's HTML and convert it into a fully enhanced, interactive website.

---

## Project Structure

```
website_converter/
├── main.py              ← FastAPI backend (all API routes)
├── requirements.txt     ← Python dependencies
├── README.md
└── static/
    └── index.html       ← Frontend UI (served by FastAPI)
```

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
uvicorn main:app --reload --port 8000
```

### 3. Open in browser
```
http://localhost:8000
```

---

## API Endpoints

| Method | Endpoint      | Description                              |
|--------|---------------|------------------------------------------|
| GET    | `/`           | Serves the frontend UI                   |
| POST   | `/api/fetch`  | Fetches & parses HTML from a URL         |
| POST   | `/api/convert`| Sends content to Claude AI for conversion|

### POST /api/fetch
**Request:**
```json
{ "url": "https://example.com" }
```
**Response:**
```json
{
  "url": "https://example.com",
  "statusCode": 200,
  "title": "Example Domain",
  "htmlLength": 1256,
  "htmlPreview": "<!doctype html>...",
  "mainContent": "Example Domain\nThis domain is for use...",
  "tags": {
    "hasDoctype": true,
    "hasHtml": true,
    "hasHead": true,
    "hasBody": true,
    "hasTitle": true,
    "hasNav": false,
    "hasFooter": false,
    "hasImages": false,
    "linkCount": 1,
    "tagCount": 12
  }
}
```

### POST /api/convert
**Request:**
```json
{
  "url": "https://example.com",
  "html_content": "Example Domain\nThis domain is for use in illustrative examples..."
}
```
**Response:**
```json
{ "generatedHTML": "<!DOCTYPE html><html>...</html>" }
```

---

## Tech Stack

| Layer     | Technology              |
|-----------|-------------------------|
| Backend   | Python, FastAPI, uvicorn|
| HTTP      | httpx (async)           |
| Parsing   | BeautifulSoup4          |
| AI        | Anthropic Claude API    |
| Frontend  | HTML, CSS, Vanilla JS   |
| Serving   | FastAPI StaticFiles     |
