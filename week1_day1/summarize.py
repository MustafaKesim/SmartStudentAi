# Day 1: summarize a text using the Gemini API

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

# use the script's own folder so this works regardless of the current directory
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "input.txt")

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

prompt = f"Summarize the following text in 2-3 sentences:\n\n{text}"
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

print(response.text)
