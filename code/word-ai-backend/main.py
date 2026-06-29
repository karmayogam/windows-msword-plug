import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def log(stage: str, msg: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {stage}" + (f" — {msg}" if msg else ""), flush=True)

class RewriteRequest(BaseModel):
    text: str
    instructions: str = ""

class FinalizeRequest(BaseModel):
    text: str
    answer: str
    instructions: str = ""

class TableRequest(BaseModel):
    text: str
    instructions: str = ""


def system_block(instructions: str) -> str:
    if instructions.strip():
        return f"[Agent Instructions]\n{instructions.strip()}\n\n"
    return ""


@app.post("/rewrite")
async def rewrite(req: Request, request: RewriteRequest):
    client_ip = req.client.host
    log("REQUEST  /rewrite", f"from {client_ip} | text: '{request.text[:60]}...'")
    log("REPLY    /rewrite", "returning tone question to client")
    return {
        "type": "question",
        "question": "What tone do you prefer?",
        "options": ["Formal", "Casual", "Concise"]
    }


@app.post("/rewrite/finalize")
async def finalize(req: Request, request: FinalizeRequest):
    client_ip = req.client.host
    log("REQUEST  /rewrite/finalize", f"from {client_ip} | tone: '{request.answer}' | text: '{request.text[:60]}...'")
    prompt = (
        f"{system_block(request.instructions)}"
        f"Rephrase the following text in a {request.answer} tone. "
        f"Return only the rephrased text, nothing else:\n\n{request.text}"
    )
    log("GEMINI   sending", f"prompt length: {len(prompt)} chars")
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    log("GEMINI   received", f"response length: {len(response.text)} chars")
    log("REPLY    /rewrite/finalize", f"returning rewritten text to {client_ip}")
    return {"type": "result", "rewrittenText": response.text}


@app.post("/make-table")
async def make_table(req: Request, request: TableRequest):
    client_ip = req.client.host
    log("REQUEST  /make-table", f"from {client_ip} | text: '{request.text[:60]}...'")
    prompt = (
        f"{system_block(request.instructions)}"
        f"""Analyze the following text and convert it into a structured table.
Return ONLY a valid JSON object in this exact format, no explanation:
{{
  "headers": ["Column1", "Column2", "Column3"],
  "rows": [
    ["value1", "value2", "value3"],
    ["value4", "value5", "value6"]
  ]
}}

Text to convert:
{request.text}"""
    )
    log("GEMINI   sending", f"prompt length: {len(prompt)} chars")
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    log("GEMINI   received", f"response length: {len(response.text)} chars")
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    table_data = json.loads(raw.strip())
    log("REPLY    /make-table", f"returning table {len(table_data['headers'])} cols x {len(table_data['rows'])} rows to {client_ip}")
    return {"type": "table", "headers": table_data["headers"], "rows": table_data["rows"]}


@app.get("/health")
async def health():
    log("REQUEST  /health", "ping")
    return {"status": "ok"}
