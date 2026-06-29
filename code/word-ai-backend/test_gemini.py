import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

text = "the quick brown fox jumps over the lazy dog"
prompt = f"Rephrase the following text to make it clearer and more professional. Return only the rephrased text, nothing else:\n\n{text}"

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt
)

print("Original :", text)
print("Rephrased:", response.text)
