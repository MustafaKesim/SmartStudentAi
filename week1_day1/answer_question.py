# Week 2, Day 2 (bonus): Answer a question about a text using the Gemini API
# We will fill this in step by step.

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads the .env file and loads its variables into the environment
api_key = os.getenv("GEMINI_API_KEY")  # reads the key from the environment

client = genai.Client(api_key=api_key)  # creates a client authenticated with this key

# Read the source text from the same input.txt file we used for summarizing.
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "input.txt")

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

# Ask the student for their question (a single line, so input() works fine here)
# Keep looping until the student types "exit"
while True:
    question = input("What is your question about this text? (type 'exit' to quit)\n")

    if question.strip().lower() == "exit":
        break

    # Build the request: give the model the material as context, the student's
    # question, and explicitly allow it to use its own broader knowledge too
    # (not just what's in the text) so it can give a full, helpful explanation.
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