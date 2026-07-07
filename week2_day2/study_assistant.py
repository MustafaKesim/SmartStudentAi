"""
Combined study assistant: summarize, answer questions, and generate a quiz
from a PDF file, using the Gemini API.

Requires a .env file with GEMINI_API_KEY set.
Run: python study_assistant.py
"""

import os
import sys
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(script_dir, "CENG 202. _Week5. Lecture 10-Stack.pdf")

reader = PdfReader(pdf_path)
text = ""
for page in reader.pages:
    text += page.extract_text()


def summarize():
    prompt = f"Summarize the following text in 2-3 sentences:\n\n{text}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    print(response.text)


def answer_question():
    question = input("What is your question about this text?\n")

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


def generate_quiz():
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


while True:
    print("\nWhat would you like to do?")
    print("1) Summarize")
    print("2) Ask a question")
    print("3) Generate a quiz")
    print("4) Exit")

    choice = input("Choose an option (1-4): ").strip()

    if choice == "1":
        summarize()
    elif choice == "2":
        answer_question()
    elif choice == "3":
        generate_quiz()
    elif choice == "4":
        break
    else:
        print("Invalid option, please try again.")
