import json
import os
import re
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI
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
async def rewrite(request: RewriteRequest):
    return {
        "type": "question",
        "question": "What tone do you prefer?",
        "options": ["Formal", "Casual", "Concise"]
    }


@app.post("/rewrite/finalize")
async def finalize(request: FinalizeRequest):
    prompt = (
        f"{system_block(request.instructions)}"
        f"Rephrase the following text in a {request.answer} tone. "
        f"Return only the rephrased text, nothing else:\n\n{request.text}"
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    return {"type": "result", "rewrittenText": response.text}


@app.post("/make-table")
async def make_table(request: TableRequest):
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
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    table_data = json.loads(raw.strip())
    return {"type": "table", "headers": table_data["headers"], "rows": table_data["rows"]}


@app.get("/health")
async def health():
    return {"status": "ok"}
