"""
Smart Student Assistant backend: upload a PDF and get a summary, ask
questions about it, or generate a quiz from it, using the Gemini API.

Requires a .env file with GEMINI_API_KEY and the DB_* PostgreSQL variables
set (see database.py).
Run: uvicorn main:app --reload
"""

import os
from fastapi import FastAPI, UploadFile, Request, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
from google.genai import types
import io

from ai import generate_content
from chunking import PAGE_DELIMITER, compute_chunks
from database import get_connection
from session import get_owner_id, get_current_document
from models import (
    SummarizePartRequest,
    QuestionRequest,
    QuizResponse,
    ActivateConversationRequest,
)

app = FastAPI()

script_dir = os.path.dirname(os.path.abspath(__file__))

# Serves style.css and app.js directly, so index.html can link/script to
# them under /static/... instead of everything being inlined in one file.
app.mount("/static", StaticFiles(directory=os.path.join(script_dir, "static")), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(script_dir, "static", "index.html"))


@app.post("/upload")
async def upload_pdf(file: UploadFile, request: Request, response: Response):
    owner_id = get_owner_id(request, response)
    contents = await file.read()
    reader = PdfReader(io.BytesIO(contents))
    pages = [page.extract_text() for page in reader.pages]
    text = PAGE_DELIMITER.join(pages)

    conversation_id = request.cookies.get("conversation_id")

    conn = get_connection()
    cur = conn.cursor()

    if conversation_id is not None:
        cur.execute(
            "SELECT id FROM conversations WHERE id = %s AND owner_id = %s",
            (conversation_id, owner_id),
        )
        if cur.fetchone() is None:
            # The conversation_id cookie doesn't belong to this owner (either
            # tampered with, or stale) -- ignore it and start a fresh chat.
            conversation_id = None

    if conversation_id is None:
        cur.execute(
            "INSERT INTO conversations (owner_id, title) VALUES (%s, %s) RETURNING id",
            (owner_id, file.filename),
        )
        conversation_id = cur.fetchone()[0]
        response.set_cookie("conversation_id", str(conversation_id), httponly=True)

    cur.execute(
        "INSERT INTO documents (conversation_id, file_name, content) VALUES (%s, %s, %s)",
        (conversation_id, file.filename, text),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "File uploaded successfully", "characters_extracted": len(text)}


@app.post("/summarize-part")
def summarize_part(body: SummarizePartRequest, request: Request, response: Response):
    owner_id = get_owner_id(request, response)
    document_id, content = get_current_document(request, owner_id)

    pages = content.split(PAGE_DELIMITER)
    chunks = compute_chunks(len(pages))

    if body.part_index < 0 or body.part_index >= len(chunks):
        raise HTTPException(status_code=400, detail="Invalid part index.")

    start, end = chunks[body.part_index]

    conn = get_connection()
    cur = conn.cursor()

    # If this exact part was already explained for this document before,
    # reuse it -- no need to spend Gemini quota generating it again.
    cur.execute(
        "SELECT output FROM results WHERE document_id = %s AND type = 'summary' AND part_index = %s",
        (document_id, body.part_index),
    )
    cached = cur.fetchone()

    if cached is not None:
        summary_text = cached[0]
    else:
        part_text = "\n\n".join(pages[start:end])

        prompt = f"""You are a study assistant walking a student through their
lecture material section by section, the way a student would study a slide
deck a chunk at a time.

Here is this section (pages {start + 1}-{end} of {len(pages)} total):
{part_text}

Explain this section clearly and thoroughly so the student fully understands
it before moving on to the next section. Do not limit yourself to a fixed
number of sentences -- cover everything meaningful in this section."""

        ai_response = generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        summary_text = ai_response.text

        cur.execute(
            "INSERT INTO results (document_id, type, part_index, output) VALUES (%s, %s, %s, %s)",
            (document_id, "summary", body.part_index, summary_text),
        )
        conn.commit()

    cur.close()
    conn.close()

    return {
        "summary": summary_text,
        "part_index": body.part_index,
        "total_parts": len(chunks),
        "start_page": start + 1,
        "end_page": end,
    }


@app.post("/ask")
def ask_question(body: QuestionRequest, request: Request, response: Response):
    owner_id = get_owner_id(request, response)
    document_id, content = get_current_document(request, owner_id)
    # /ask always sees the whole document, so the page-chunk markers (only
    # meaningful to the Summarize feature) would just be noise here.
    content = content.replace(PAGE_DELIMITER, "\n\n")

    prompt = f"""You are a study assistant helping a student understand their course material.

Here is the material the student is studying:
{content}

The student's question:
{body.question}

Answer the question clearly and completely. Use the material above as context,
but you are not limited to it -- feel free to use your own broader knowledge
to give the most helpful and accurate answer."""

    ai_response = generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO results (document_id, type, question, output) VALUES (%s, %s, %s, %s)",
        (document_id, "answer", body.question, ai_response.text),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"answer": ai_response.text}


@app.post("/quiz")
def generate_quiz(request: Request, response: Response):
    owner_id = get_owner_id(request, response)
    document_id, content = get_current_document(request, owner_id)
    content = content.replace(PAGE_DELIMITER, "\n\n")

    prompt = f"""You are a study assistant creating a quiz for a student.

Here is the material to base the quiz on:
{content}

Generate 5 multiple-choice questions based on this material. Each question
should have exactly 4 options, and correct_answer must be exactly one of:
"A", "B", "C", "D"."""

    ai_response = generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuizResponse,
        ),
    )

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO results (document_id, type, output) VALUES (%s, %s, %s)",
        (document_id, "quiz", ai_response.text),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"quiz": ai_response.parsed.model_dump()}


@app.post("/new-chat")
def new_chat(response: Response):
    response.delete_cookie("conversation_id")
    return {"message": "Started a new chat"}


@app.post("/activate-conversation")
def activate_conversation(body: ActivateConversationRequest, request: Request, response: Response):
    owner_id = get_owner_id(request, response)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM conversations WHERE id = %s AND owner_id = %s",
        (body.conversation_id, owner_id),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    response.set_cookie("conversation_id", str(body.conversation_id), httponly=True)
    return {"message": "Conversation activated"}


@app.get("/history")
def history(request: Request, response: Response):
    owner_id = get_owner_id(request, response)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT conversations.id, conversations.title, documents.file_name,
               results.type, results.question, results.part_index,
               results.output, results.created_at
        FROM conversations
        JOIN documents ON documents.conversation_id = conversations.id
        JOIN results ON results.document_id = documents.id
        WHERE conversations.owner_id = %s
        ORDER BY conversations.created_at DESC, results.created_at ASC
        """,
        (owner_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # The query returns one row per result (a conversation with 3 results
    # comes back as 3 rows, each repeating the conversation's title) --
    # group them back into one entry per conversation, with its results
    # nested underneath, which is what the frontend actually wants to render.
    conversations = {}
    for conv_id, title, file_name, result_type, question, part_index, output, created_at in rows:
        if conv_id not in conversations:
            conversations[conv_id] = {"id": conv_id, "title": title, "results": []}
        conversations[conv_id]["results"].append({
            "type": result_type,
            "question": question,
            "part_index": part_index,
            "output": output,
            "created_at": created_at.isoformat(),
            "file_name": file_name,
        })

    return {"conversations": list(conversations.values())}
