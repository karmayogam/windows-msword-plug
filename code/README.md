# Windows MS Word AI Plugin — POC

A Microsoft Word Add-in (via Script Lab) that connects to a FastAPI + Google Gemini backend to bring AI capabilities directly into Word's task pane.

---

## What This Does

- **AI Rewrite** — Select a paragraph in Word, choose a tone (Formal / Casual / Concise), and the LLM rewrites it in place.
- **Make Table** — Select unstructured text, and the LLM converts it into a real Word table (not markdown — actual Office table with styling).
- **Agent Instructions** — Set a system prompt once; it is automatically prepended to every LLM call, giving the agent persistent context and behavior.
- **Multi-page Navigation** — Task pane works as a SPA (Single Page Application) with 4 pages and back/forward navigation.

---

## Architecture

```
MS Word (Task Pane / Script Lab)
    └── Embedded Browser — HTML/JS/CSS
            ├── Office.js  →  read / write Word document
            └── fetch()    →  FastAPI backend (HTTPS)
                                    └── Google Gemini API
```

The task pane is an embedded browser (WebView2). `Office.js` is the bridge that lets the webpage read and write Word document content. All AI logic lives in the FastAPI backend — Word is the UI shell.

---

## Project Structure

```
code/
├── word-ai-backend/
│   ├── main.py              # FastAPI app — all API endpoints
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # GEMINI_API_KEY — never committed
│   └── word-ai-backend/     # Python virtual environment
│
└── word-ai-addin/
    ├── snippet.yaml         # Script Lab snippet — source of truth
    └── manifest.xml         # Office Add-in manifest (for future production deployment)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rewrite` | Returns tone choice question |
| POST | `/rewrite/finalize` | Rewrites text with chosen tone via Gemini |
| POST | `/make-table` | Converts text to JSON table data via Gemini |
| GET | `/health` | Health check |

All POST endpoints accept an `instructions` field — the agent system prompt set by the user.

---

## Setup

### 1. Backend

```bash
cd code/word-ai-backend
python3 -m venv word-ai-backend
source word-ai-backend/bin/activate
pip install -r requirements.txt
```

Create `.env` file:
```
GEMINI_API_KEY=your_key_here
```

Run:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 \
  --ssl-certfile ../192.168.16.62.pem \
  --ssl-keyfile ../192.168.16.62-key.pem
```

### 2. Add-in File Server

```bash
cd code
http-server word-ai-addin -p 3000 --ssl \
  --cert 192.168.16.62.pem \
  --key 192.168.16.62-key.pem
```

### 3. Script Lab (MS Word)

1. Word → Insert → Add-ins → Search **"Script Lab"** → Install
2. Script Lab → New Snippet
3. Copy HTML from `snippet.yaml` (under `template: content:`) → paste into HTML tab
4. Copy JS from `snippet.yaml` (under `script: content:`) → paste into JS tab
5. Clear CSS tab → Run

> **Note:** Script Lab YAML import from URL has a caching issue with complex HTML templates. Direct paste into the HTML/JS tabs is the reliable approach.

---

## Security

- API key is stored only in `.env` — never hardcoded, never committed
- `.env` is listed in `.gitignore`
- Backend uses HTTPS with self-signed SSL certs (for local network POC)

---

## Dependencies

```
fastapi==0.138.0
uvicorn==0.49.0
google-genai
python-dotenv
```

---

## Key Insight

> A Word Add-in is just **web technology + Office.js bridge**. Anything a webpage can do, the task pane can do — chat UI, dashboards, forms, API calls. The bridge gives access to document content. This pattern can extend to: document summarization, proposal generation, auto-formatting, chatbot, and any workflow where document content needs to interact with AI.
