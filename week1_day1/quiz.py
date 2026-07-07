# Week 1, Day 1 (bonus): Generate quiz questions from a text using the Gemini API
# We will fill this in step by step.

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads the .env file and loads its variables into the environment
api_key = os.getenv("GEMINI_API_KEY")  # reads the key from the environment

client = genai.Client(api_key=api_key)  # creates a client authenticated with this key

# Read the source text from the same input.txt file we used before.
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "input.txt")

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

# Build the request: ask the model to generate multiple-choice questions
# based on the material, each with 4 options and the correct answer marked.
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
