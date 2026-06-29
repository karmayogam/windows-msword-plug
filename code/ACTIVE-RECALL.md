# Active Recall — MS Word AI Plugin POC

> இந்த questions-ஐ answer பண்ண try பண்ணுங்க — அப்புறம் மட்டுமே explanation பாருங்க.
> தினமும் 5 questions — 3 நாள்ல எல்லாம் cover ஆகும்.

---

## SECTION 1 — Basic (What did we build?)

---

**Q1. இந்த POC-ல் நாம் என்ன build பண்ணோம்? ஒரே வரியில் சொல்லுங்க.**

<details>
<summary>Answer</summary>

Microsoft Word-ஓட Task Pane-ல் ஒரு AI-powered web app — user selected text-ஐ Gemini LLM-கிட்ட அனுப்பி rewrite பண்ணவும், real Word table create பண்ணவும் use பண்ணோம்.

</details>

---

**Q2. எந்த LLM model use பண்ணோம்? ஏன் அந்த specific model?**

<details>
<summary>Answer</summary>

`gemini-2.5-flash-lite` — Google-ஓட fastest, cheapest variant. POC-க்கு speed + cost important, accuracy secondary. Production-க்கு போனா `gemini-2.5-pro`-க்கு upgrade பண்ணலாம்.

- **Flash** = low latency (response fast-ஆ வரும்)
- **Lite** = lightest variant — simple tasks like rewrite, table conversion போதும்
- **2.5** = latest generation

</details>

---

**Q3. Script Lab என்றால் என்ன? ஏன் use பண்ணோம்?**

<details>
<summary>Answer</summary>

Script Lab = Microsoft-ஓட Word Add-in, அதுல HTML/JS/CSS directly எழுதி Word-ல் run பண்ணலாம் — deployment இல்லாம, manifest இல்லாம. POC-க்கு perfect shortcut. Browser-ல் CodePen மாதிரி, ஆனால் Word-க்கு inside.

Production Add-in build பண்ண வேணும்னா manifest.xml + HTTPS hosting தேவை. Script Lab அதை bypass பண்றது.

</details>

---

**Q4. snippet.yaml என்றால் என்ன? ஏன் அந்த file create பண்ணோம்?**

<details>
<summary>Answer</summary>

Script Lab-ல் நாம் type பண்ற HTML + JS + CSS-ஐ ஒரே file-ல் bundle பண்ணி save பண்ணது. Script Lab-ஓட format இது.

ஏன் தேவை: Script Lab content browser-ஓட local storage-ல் மட்டும் இருக்கும் — clear ஆனா போச்சு. `snippet.yaml`-ல் save பண்ணினா git-ல் track ஆகும், எந்த machine-லயும் restore பண்ணலாம்.

</details>

---

## SECTION 2 — Architecture (Why did we structure it this way?)

---

**Q5. நாம் ஏன் two servers run பண்றோம்? ஒன்னு போதாதா?**

<details>
<summary>Answer</summary>

இரண்டும் different roles:

| Port | Server | Role |
|------|--------|------|
| 8000 | FastAPI (Python) | AI logic — Gemini call, response process |
| 3000 | http-server (Node) | Static file serve — snippet.yaml deliver |

Port 3000 Script Lab-கு snippet.yaml கொடுக்க மட்டும். நம் POC-ல் YAML import fail ஆச்சு (cache issue), so port 3000 actually unnecessary ஆச்சு — direct paste use பண்றோம். Port 8000 மட்டும் essential.

</details>

---

**Q6. Word Add-in என்பது architecturally என்ன? Office.js என்றால் என்ன?**

<details>
<summary>Answer</summary>

Word-ஓட Task Pane = embedded browser (WebView2). அதுல எந்த webpage-உம் run ஆகும். So Word Add-in = **Web Technology inside Word**.

`Office.js` = bridge (பாலம்). அந்த bridge மூலம் webpage Word document-ஓட content read/write பண்ண முடியும்:
- Selected text எடுக்கலாம்
- Text insert/replace பண்ணலாம்  
- Real table create பண்ணலாம்
- Document metadata படிக்கலாம்

இல்லாம்னா webpage-க்கும் Word-க்கும் எந்த connection-உம் இல்லை.

</details>

---

**Q7. SPA navigation என்றால் என்ன? நாம் எப்படி implement பண்ணோம்?**

<details>
<summary>Answer</summary>

SPA = Single Page Application — actual page reload இல்லாம, ஒரே HTML page-ல் multiple "views" show/hide பண்றது.

நாம் 4 `<div>` create பண்ணோம் — home, form, rewrite, table. ஒரு div மட்டும் `display:block`, மற்றவை `display:none`. Button click-ல் `showPage()` function-ல் switch பண்றோம்.

ஏன் இந்த approach: Task Pane-ல் actual page navigation இல்லை — URL change ஆகாது, iframe reload ஆகாது. SPA pattern-மட்டுமே work பண்ணும்.

</details>

---

**Q8. Agent Instructions feature எப்படி work பண்றது? System prompt எங்க போகுது?**

<details>
<summary>Answer</summary>

User ஒரு முறை Agent Instructions page-ல் type பண்ணுவாங்க. அது JS variable-ல் save ஆகும்:

```javascript
agentContext = { instructions: "You are a formal technical writer..." }
```

எல்லா fetch() call-லயும் இந்த `instructions` field send ஆகும். Backend-ல் `system_block()` function அதை Gemini prompt-ஓட beginning-ல் prepend பண்ணும்:

```
[Agent Instructions]
You are a formal technical writer...

Rephrase the following text...
```

Gemini-க்கு context-ஆ போகுது — user behavior ஒரே முறை define பண்ணா போதும், எல்லா calls-லயும் automatically apply ஆகும்.

</details>

---

## SECTION 3 — Security Decisions

---

**Q9. ஏன் HTTPS mandatory? HTTP use பண்ணக்கூடாதா?**

<details>
<summary>Answer</summary>

Word-ஓட Task Pane = WebView2 (embedded Edge browser). Modern browsers HTTP calls-ஐ **Mixed Content** policy-ல் block பண்றது — HTTPS page-இருந்து HTTP call பண்ண allow பண்றதில்லை.

நம் case-ல்: Script Lab HTTPS-ல் serve ஆகுது. அந்த page-இருந்து backend-க்கு HTTP call பண்ணா browser block பண்ணும். So backend-உம் HTTPS-ல் இருக்கணும்.

கூடவே: Real network-ல் HTTP = plain text — API key, document content எல்லாம் visible. HTTPS = encrypted.

</details>

---

**Q10. API key-ஐ code-ல் hardcode பண்ணாம `.env`-ல் வைக்க வேண்டியதன் reason என்ன?**

<details>
<summary>Answer</summary>

Code-ல் hardcode பண்ணினா:
1. Git-ல் commit ஆகும் — history-ல் forever இருக்கும், even after delete
2. GitHub public repo-ல் இருந்தா bots immediately scan பண்ணி key steal பண்ணும்
3. Team member-கிட்ட code share பண்ணும்போது key-உம் போகும்

`.env` approach:
- `.gitignore`-ல் list பண்ணினா never commit ஆகாது
- `python-dotenv` load பண்றது — `os.environ["GEMINI_API_KEY"]`
- Different machines-ல் different keys — production key different, dev key different

Rule: **Secret = never in code. Always in environment.**

</details>

---

**Q11. mkcert ஏன் use பண்ணோம்? openssl போதாதா?**

<details>
<summary>Answer</summary>

`openssl` self-signed cert generate பண்ணும் — ஆனால் browser அதை trust பண்றதில்லை (red warning screen). நாம் manually browser-ல் "proceed anyway" click பண்ணணும் — Word-ஓட WebView2-ல் அந்த option கூட இல்லை, silently block ஆகும்.

`mkcert` வேற approach:
1. Local Certificate Authority (CA) create பண்றது
2. அந்த CA-ஐ OS trust store-ல் install பண்றது
3. அந்த CA மூலம் cert issue பண்றது

OS trust பண்றதால் browser automatically trust பண்றது — no warnings, no manual steps. Local development-க்கு perfect.

</details>

---

## SECTION 4 — Deep Technical Decisions

---

**Q12. LLM-கிட்ட table create பண்ணச் சொல்லும்போது, ஏன் markdown table return பண்ணச் சொல்லல? JSON-ஆ கேட்டோம் — why?**

<details>
<summary>Answer</summary>

Markdown table (`| col | col |`) return பண்ணினா:
- அது plain text — Word-ல் paste பண்ணினா formatting இல்லாம text-ஆ வரும்
- Word real table-ஆ automatically convert பண்றதில்லை

JSON return பண்ணினா:
```json
{"headers": ["Name", "Age"], "rows": [["John", "25"]]}
```
- Backend parse பண்ணலாம்
- `Office.js`-ஓட `insertTable()` API-க்கு values array pass பண்ணலாம்
- Real Word table create ஆகும் — styled, formatted, editable

**Key insight:** LLM output-ஐ structured data-ஆ force பண்ணினால்மட்டுமே programmatically process பண்ண முடியும்.

</details>

---

**Q13. YAML import-ல் ஏன் error வந்தது? Root cause என்ன?**

<details>
<summary>Answer</summary>

Script Lab YAML import பண்ணும்போது internally `element.innerHTML = parsedYamlContent` பண்றது.

நம் HTML-ல்: `onclick="showPage('page-form')"` — double quotes-க்கு inside single quotes இருக்கு. YAML parser இந்த nested quotes-ஐ parse பண்ணும்போது content corrupt ஆகுது. Corrupt HTML-ஐ innerHTML-ல் set பண்ண try பண்ணும்போது Script Lab crash ஆகுது.

**Fix:** Direct paste — YAML parsing bypass ஆகும், CodeMirror editor directly content receive பண்றது.

**Lesson:** YAML-ல் complex HTML embed பண்ணும்போது quoting issues common. Production Add-in-ல் இந்த problem இல்லை — manifest + hosted HTML file use பண்றோம்.

</details>

---

**Q14. Make Table flow-ல் backend என்ன exactly பண்றது? Step by step சொல்லுங்க.**

<details>
<summary>Answer</summary>

1. Word-ல் text select → JS `makeTable()` call
2. `Office.js` selection.text read பண்றது
3. `fetch('/make-table')` → FastAPI
4. FastAPI Gemini-கிட்ட prompt அனுப்புது: "Return ONLY JSON with headers and rows"
5. Gemini JSON return பண்றது (sometimes markdown fences-ல் wrap பண்றது)
6. Backend regex-ல் ` ```json ` fences strip பண்றது
7. `json.loads()` parse பண்றது
8. `{"headers": [...], "rows": [[...]]}` return பண்றது
9. JS `insertTable(rowCount, colCount, "Before", values)` call
10. `table.styleBuiltIn = gridTable4Accent1` — Word built-in style apply
11. Real formatted table Word-ல் appear ஆகுது

Critical step: Step 6 — Gemini always instructions follow பண்றதில்லை, sometimes extra text add பண்றது. Regex strip பண்ணாம்னா `json.loads()` fail ஆகும்.

</details>

---

**Q15. Debug logging-ல் நாம் என்ன log பண்றோம்? ஏன் அந்த specific information?**

<details>
<summary>Answer</summary>

ஒவ்வொரு request-லயும் 4 log lines:

```
[time] REQUEST  /endpoint  — from <IP> | text preview
[time] GEMINI   sending    — prompt length
[time] GEMINI   received   — response length  
[time] REPLY    /endpoint  — table size / result to <IP>
```

**ஏன் இந்த information:**
- `client IP` — Word எந்த machine-இருந்து call பண்றதுன்னு confirm
- `text preview` — correct text select ஆச்சான்னு verify
- `prompt length` — unexpectedly large prompt போகுதான்னு catch
- `response length` — Gemini empty/truncated response return பண்ணாலு catch
- `table size` — rows x cols correct-ஆ parse ஆச்சான்னு confirm

Production-ல் இதை structured logging (JSON format) + log aggregator (e.g. CloudWatch) மாத்தலாம்.

</details>

---

**Q16. FastAPI-ல் `Request` object-ஐ ஏன் parameter-ஆ add பண்ணோம்?**

<details>
<summary>Answer</summary>

Client-ஓட IP address எடுக்கணும்னா `req.client.host` தேவை. அது `fastapi.Request` object-ல் மட்டுமே இருக்கும்.

```python
async def make_table(req: Request, request: TableRequest):
    client_ip = req.client.host
```

Pydantic model (`TableRequest`) body data மட்டும் parse பண்றது — HTTP metadata (IP, headers, method) அதுல இல்லை. `Request` object = raw HTTP request details.

</details>

---

## SECTION 5 — Concepts (Understand the Why)

---

**Q17. TLS Handshake-ல் Session Key network-ல் போவதில்லை — இது எப்படி possible?**

<details>
<summary>Answer</summary>

Magic of **Pre-Master Secret + Derivation:**

1. Client ஒரு random Pre-Master Secret generate பண்றது
2. Server-ஓட Public Key-ல் encrypt பண்ணி அனுப்புது
3. Server Private Key-ல் decrypt பண்றது → Pre-Master Secret கிடைக்குது
4. **இருவரும் independently** — Pre-Master Secret + ClientRandom + ServerRandom → Session Key derive பண்றாங்க (same formula, same inputs → same output)

Session Key network-ல் போகவே இல்லை — இரண்டு sides-லயும் independently calculate ஆகுது. Network-ல் போவது encrypted Pre-Master Secret மட்டும் — அதை Private Key இல்லாம யாரும் decrypt பண்ண முடியாது.

</details>

---

**Q18. Word Add-in-ஐ production-க்கு எடுத்துக்கணும்னா Script Lab-இருந்து என்ன மாத்தணும்?**

<details>
<summary>Answer</summary>

Script Lab = development/POC tool மட்டும். Production-க்கு:

1. **manifest.xml** — Add-in-ஓட identity, permissions, task pane URL define பண்றது. நம்மிடம் already இருக்கு.
2. **Hosted HTML/JS** — snippet.yaml-ல் இருக்கற code-ஐ real HTML file-ஆ convert பண்ணி HTTPS server-ல் host பண்ணணும்.
3. **Office Store / Sideloading** — manifest-ஐ org-ல் deploy பண்ணணும் (IT admin மூலம்) அல்லது Microsoft Store-ல் publish பண்ணணும்.

Core logic (FastAPI backend, Gemini integration) மாறாது — frontend hosting மட்டும் மாறும்.

</details>

---

---

## SECTION 6 — Technology Choices (Why this tool, not that tool?)

---

**Q19. ஏன் FastAPI? Flask அல்லது Django use பண்ணக்கூடாதா?**

<details>
<summary>Answer</summary>

**Flask:** Minimal framework — good, ஆனால் async support இல்லை by default. நாம் Gemini API call பண்றோம் — I/O-bound operation. Async இல்லாம்னா ஒரு request Gemini-ஐ wait பண்றப்போ next request block ஆகும்.

**Django:** Full-stack framework — ORM, admin panel, templating எல்லாம் இருக்கு. நமக்கு ஒரு simple API மட்டும் தேவை. Django overkill — unnecessary complexity.

**FastAPI:**
- `async/await` native support — Gemini call wait பண்றப்போ மற்ற requests handle ஆகும்
- Pydantic models — request body automatically validate ஆகும் (type errors early catch)
- Auto-generated `/docs` (Swagger UI) — API test பண்ண browser போதும்
- Modern Python — type hints first-class citizen

**What if we had used Flask:** Single user POC-ல் difference தெரியாது. Multiple users simultaneously use பண்ணும்போது Flask block ஆகும், FastAPI handle பண்ணும்.

</details>

---

**Q20. இந்த POC-ல் nginx இல்லை — production-ல் nginx ஏன் தேவை? அது என்ன பண்றது?**

<details>
<summary>Answer</summary>

nginx = **reverse proxy** (முன்னால் நிக்கற gate-keeper). Production-ல் directly FastAPI-ஐ internet-க்கு expose பண்றதில்லை. nginx-ஐ முன்னால் வைப்போம்.

**nginx என்ன பண்றது:**

1. **SSL Termination** — HTTPS connection nginx-ல் end ஆகுது. FastAPI-க்கு plain HTTP போகுது. FastAPI SSL பத்தி கவலைப்பட வேண்டாம்.

2. **Load Balancing** — Multiple FastAPI instances run பண்ணினா nginx traffic distribute பண்றது.

3. **Static File Serving** — HTML, CSS, JS files-ஐ nginx directly serve பண்றது — FastAPI-ஐ reach பண்றதே இல்லை. Fast.

4. **Rate Limiting** — ஒரே IP-இருந்து too many requests வந்தா block பண்றது.

5. **Request Buffering** — Slow client connection-ல் nginx buffer பண்றது, FastAPI-ஐ free-ஆ வைக்கிறது.

**Our POC vs Production:**
```
POC:        Word → FastAPI (8000, HTTPS directly)
Production: Word → nginx (443, HTTPS) → FastAPI (8000, HTTP, localhost only)
```

nginx இல்லாம production போனா FastAPI directly exposed — security risk, performance bottleneck.

</details>

---

**Q21. ஏன் `google-genai` package? `google-generativeai` package-உம் இருக்கே — வித்தியாசம் என்ன?**

<details>
<summary>Answer</summary>

`google-generativeai` = older package (v1 SDK). `google-genai` = new unified SDK (v2).

**Differences:**
- `google-genai` — Gemini + Imagen + future models எல்லாத்தையும் ஒரே SDK-ல் handle பண்றது
- Cleaner API: `client.models.generate_content()` vs older `genai.GenerativeModel().generate_content()`
- Better async support
- Google officially `google-genai`-க்கு migrate பண்ணச் சொல்றாங்க

நாம் `google-genai` use பண்ணோம் — future-proof, Google-recommended.

</details>

---

**Q22. ஏன் `uvicorn`? Gunicorn use பண்ணக்கூடாதா?**

<details>
<summary>Answer</summary>

**Gunicorn** = traditional WSGI (synchronous) server. FastAPI async (ASGI) framework. Gunicorn நேரடியா FastAPI run பண்ண முடியாது — ASGI adapter தேவை.

**uvicorn** = ASGI server — async Python apps-க்கு specifically designed. FastAPI + uvicorn = perfect match.

**Production pattern:** `gunicorn -k uvicorn.workers.UvicornWorker` — Gunicorn process management + uvicorn async handling. Multiple worker processes-க்கு இந்த combo use பண்றாங்க.

**Our POC:** Single uvicorn process போதும். Production-ல் `gunicorn + uvicorn workers` combo better.

</details>

---

**Q23. `python-dotenv` ஏன் தேவை? `os.environ` directly use பண்ணக்கூடாதா?**

<details>
<summary>Answer</summary>

`os.environ["GEMINI_API_KEY"]` — environment variable system-level-ல் set ஆச்சிருந்தா மட்டும் work பண்றது. `export GEMINI_API_KEY=xxx` terminal-ல் run பண்ணணும் — deploy பண்ணும்போது forget ஆகும், CI/CD-ல் extra steps தேவை.

`python-dotenv` — `.env` file-ஐ automatically read பண்ணி `os.environ`-ல் load பண்றது. Code-ல் ஒரே line: `load_dotenv()`. `.env` file project folder-ல் இருந்தா automatically pick up ஆகும்.

**Benefit:** Developer எந்த extra terminal setup-உம் இல்லாம project clone பண்ணி `.env` create பண்ணி run பண்ணலாம். Team-friendly, portable.

</details>

---

**Q24. WebView2 என்றால் என்ன? Word-ல் எப்படி use ஆகுது?**

<details>
<summary>Answer</summary>

WebView2 = Microsoft-ஓட embedded browser component — Edge (Chromium)-ஐ அடிப்படையாக வச்சது. Windows applications-ல் web content render பண்ண use பண்றாங்க.

Word-ல்: Task Pane-ல் தெரியற எல்லாமே WebView2-ல் render ஆகுது. அதாவது Word-ஓட task pane = Edge browser window, Word application-க்கு inside embed பண்ணது.

**Why it matters for us:**
- Modern CSS/JS features support ஆகும் (flex, async/await, fetch)
- HTTPS-only policy enforce ஆகும் (mixed content blocked)
- `Office.js` bridge இந்த WebView2 + Word native code-க்கு நடுவில் இயங்குது
- F12 DevTools directly work பண்றதில்லை (special flags தேவை)

</details>

---

**Q25. இந்த POC-ல் நாம் use பண்ண `Office.js insertTable()` alternative என்ன? ஏன் அதை choose பண்ணோம்?**

<details>
<summary>Answer</summary>

**Alternative 1 — insertText() with markdown:** `| col | col |` text insert பண்றது. Word real table-ஆ render பண்றதில்லை — plain text மட்டுமே.

**Alternative 2 — Open XML manipulation:** Word document XML directly edit பண்றது. Powerful ஆனால் extremely complex — table XML structure manually எழுதணும்.

**Alternative 3 — insertTable() (what we chose):** Office.js high-level API. Values array pass பண்ணினா Office automatically real table create பண்றது. Style (`gridTable4Accent1`) ஒரே line-ல் apply ஆகுது.

**Why insertTable():** Simplest, most reliable, Office-native. LLM JSON output-ஐ directly values array-ஆ use பண்ணலாம். No XML knowledge தேவை.

</details>

---

*Total: 25 questions — Basic (4) + Architecture (4) + Security (3) + Deep Technical (5) + Technology Choices (7) + Concepts (2)*

*Next step: இதை PDF-ஆ convert பண்ண script எழுதலாம் — `markdown → PDF` via `weasyprint` or `pandoc`.*
