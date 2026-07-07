"""
Answers a student's questions about a text file (input.txt) using the Gemini
API. Not limited to the text -- the model can also draw on its own broader
knowledge to give a fuller answer.

Requires a .env file with GEMINI_API_KEY set.
Run: python answer_question.py
Type 'exit' to quit.
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

while True:
    question = input("What is your question about this text? (type 'exit' to quit)\n")

    if question.strip().lower() == "exit":
        break

    # not limited to the text -- model can use its own knowledge too
    prompt = f"""You are a study assistant helping a student understand their course material.

Here is the material the student is studying:
{text}

The student's question:
{question}

Answer the question clearly and completely. Use the material above as context,
but you are not limited to it -- feel free to use your own broader knowledge
to give the most helpful and accurate answer."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    print(response.text)