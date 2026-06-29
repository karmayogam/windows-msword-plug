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
            └── fetch()    →  FastAPI backend (HTTPS, port 8000)

FastAPI Backend (port 8000)
    └── Google Gemini API (gemini-2.5-flash-lite)
```

The task pane is an embedded browser (WebView2). `Office.js` is the bridge that lets the webpage read and write Word document content. All AI logic lives in the FastAPI backend — Word is just the UI shell.

---

## Why Two Ports?

| Port | What runs | Purpose |
|------|-----------|---------|
| **8000** | FastAPI (Python) | Receives requests from Word, calls Gemini, returns results |
| **3000** | http-server (Node) | Serves `snippet.yaml` so Script Lab can import it via URL |

**Why HTTPS on both?**
Word Add-ins only allow HTTPS connections — HTTP calls are blocked by the browser security policy inside the WebView2 container. So both servers must have valid SSL certificates.

> **Note:** Port 3000 is optional if you paste HTML/JS directly into Script Lab tabs (which is the reliable approach — see Script Lab Setup below).

---

## SSL Certificate Setup

Word's embedded browser (WebView2) refuses self-signed certs by default. We use **mkcert** — a tool that creates a local trusted Certificate Authority (CA) and issues certs trusted by your machine.

### Step 1 — Install mkcert

```bash
# Ubuntu/Debian
sudo apt install mkcert

# macOS
brew install mkcert
```

### Step 2 — Install the local CA into your system trust store

```bash
mkcert -install
```

This makes your machine trust all certs issued by mkcert's local CA. The root CA files (`rootCA.pem`, `rootCA.crt`) are stored in `word-ai-addin/` for reference.

### Step 3 — Generate cert for your machine's local IP

```bash
cd code/
mkcert 192.168.16.62
```

Replace `192.168.16.62` with your machine's actual local IP (`ip addr` or `ipconfig` to find it).

This generates two files:
```
192.168.16.62.pem      ← certificate (public)
192.168.16.62-key.pem  ← private key
```

> **These files are gitignored and must never be committed.** Regenerate them on each machine using the steps above.

### Step 4 — Trust the CA on Windows (for Word)

Since Word runs on Windows and the CA was installed on Linux, you need to install the root CA on the Windows machine too:

1. Copy `rootCA.crt` to Windows
2. Double-click → Install Certificate → Local Machine → Trusted Root Certification Authorities
3. Restart Word

---

## Project Structure

```
code/
├── word-ai-backend/
│   ├── main.py              # FastAPI app — all API endpoints + debug logging
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # GEMINI_API_KEY — gitignored, never committed
│   └── word-ai-backend/     # Python virtual environment (gitignored)
│
└── word-ai-addin/
    ├── snippet.yaml         # Script Lab snippet — source of truth for HTML/JS/CSS
    ├── rootCA.pem           # mkcert root CA (for reference / Windows install)
    ├── rootCA.crt           # mkcert root CA in CRT format
    └── manifest.xml         # Office Add-in manifest (for future production deployment)
```

---

## Setup & Run

### 1. Backend — Python environment

```bash
cd code/word-ai-backend
python3 -m venv word-ai-backend
source word-ai-backend/bin/activate
pip install -r requirements.txt
```

### 2. Create .env file (never commit this)

```bash
# code/word-ai-backend/.env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 3. Run FastAPI backend (Terminal 1)

```bash
cd code/word-ai-backend
source word-ai-backend/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 \
  --ssl-certfile ../192.168.16.62.pem \
  --ssl-keyfile ../192.168.16.62-key.pem
```

You should see:
```
INFO: Uvicorn running on https://0.0.0.0:8000
```

### 4. Run file server for Script Lab (Terminal 2) — optional

```bash
cd code
npx http-server word-ai-addin -p 3000 --ssl \
  --cert 192.168.16.62.pem \
  --key 192.168.16.62-key.pem
```

---

## Script Lab Setup (MS Word)

### Install Script Lab
1. Word → **Insert** → **Add-ins** → Search **"Script Lab"** → **Add**
2. A **Script Lab** tab appears in the Word ribbon

### Load the snippet
1. Script Lab → **Code** → **New Snippet**
2. Open `snippet.yaml` from this repo
3. Copy everything under `template: content:` → paste into Script Lab **HTML tab**
4. Copy everything under `script: content:` → paste into Script Lab **JS tab**
5. Clear the **CSS tab**
6. Click **▶ Run**

> **Why not import from URL?**
> Script Lab's YAML import from URL has a caching issue with complex HTML templates (nested quotes in `onclick` handlers interfere with YAML parsing). Direct paste into HTML/JS tabs is the reliable approach. `snippet.yaml` is kept as source of truth for version control.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rewrite` | Returns tone choice question to Word |
| POST | `/rewrite/finalize` | Rewrites selected text with chosen tone via Gemini |
| POST | `/make-table` | Converts selected text to JSON table data via Gemini |
| GET | `/health` | Health check |

All POST endpoints accept an `instructions` field — the agent system prompt set by the user in the Agent Instructions page.

### Debug Logging

The backend prints a log line at each stage:

```
[14:32:01] REQUEST  /make-table — from 192.168.16.62 | text: 'John is 25 years old...'
[14:32:01] GEMINI   sending — prompt length: 312 chars
[14:32:03] GEMINI   received — response length: 187 chars
[14:32:03] REPLY    /make-table — returning table 3 cols x 2 rows to 192.168.16.62
```

---

## Security

- API key stored only in `.env` — never hardcoded, never committed
- `.env` and SSL certs (`*.pem`, `*.key`) are in `.gitignore`
- Backend uses HTTPS with mkcert-issued certs (trusted by local machine)

---

## Dependencies

```
# Python (requirements.txt)
fastapi==0.138.0
uvicorn==0.49.0
google-genai
python-dotenv
```

---

## Key Insight

> A Word Add-in is just **web technology + Office.js bridge**. Anything a webpage can do, the task pane can do — chat UI, dashboards, forms, API calls. The bridge gives access to document content. This pattern can extend to: document summarization, proposal generation, auto-formatting, chatbot, and any workflow where document content needs to interact with AI.
