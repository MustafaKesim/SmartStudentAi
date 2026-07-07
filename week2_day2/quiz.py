"""
Generates multiple-choice quiz questions from a text file (input.txt)
using the Gemini API.

Requires a .env file with GEMINI_API_KEY set.
Run: python quiz.py
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "input.txt")

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

prompt = f"""You are a study assistant creating a quiz for a student.

Here is the material to base the quiz on:
{text}

Generate 3 multiple-choice questions based on this material.
Each question should have 4 options labeled A, B, C, D.
After each question, clearly indicate the correct answer."""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

print(response.text)
