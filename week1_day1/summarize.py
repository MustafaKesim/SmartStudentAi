# Week 2, Day 1: Summarize a text using the Gemini API
# We will fill this in step by step.

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads the .env file and loads its variables into the environment
api_key = os.getenv("GEMINI_API_KEY")  # reads the key from the environment

client = genai.Client(api_key=api_key)  # creates a client authenticated with this key

# Read the text we want to summarize from a file next to this script.
# Using the script's own folder (instead of a plain relative path) means
# this works no matter which folder you run the command from.
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "input.txt")

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

# Build the request: combine an instruction with the text, and send it to Gemini
prompt = f"Summarize the following text in 2-3 sentences:\n\n{text}"
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

# Print the response we got back
print(response.text)
