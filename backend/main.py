"""
Minimal FastAPI app to confirm the server runs.

Run: uvicorn main:app --reload
"""

import os
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI,UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pypdf import PdfReader
import io

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

app = FastAPI()

script_dir = os.path.dirname(os.path.abspath(__file__))


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(script_dir, "static", "index.html"))


document_text=""
@app.post("/upload")
async def upload_pdf(file:UploadFile):
    global document_text
    contents = await file.read()
    reader = PdfReader(io.BytesIO(contents))
    text = ""
    for page in reader.pages:
        text += page.extract_text()
         
    document_text=text

    return {"message": "File uploaded successfully", "characters_extracted": len(text)}


@app.post("/summarize")
def summarize():
    prompt = f"Summarize the following text in 2-3 sentences:\n\n{document_text}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return {"summary": response.text}


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_question(request: QuestionRequest):
    prompt = f"""You are a study assistant helping a student understand their course material.

Here is the material the student is studying:
{document_text}

The student's question:
{request.question}

Answer the question clearly and completely. Use the material above as context,
but you are not limited to it -- feel free to use your own broader knowledge
to give the most helpful and accurate answer."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return {"answer": response.text}

@app.post("/quiz")
def generate_quiz():
    prompt = f"""You are a study assistant creating a quiz for a student.

Here is the material to base the quiz on:
{document_text}

Generate 3 multiple-choice questions based on this material.
Each question should have 4 options labeled A, B, C, D.
After each question, clearly indicate the correct answer."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return {"quiz": response.text}