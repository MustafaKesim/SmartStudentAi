# Smart Student Assistant

An AI-powered study assistant: upload your lecture slides (PDF) and get
section-by-section summaries, ask questions about the material, and
generate an interactive quiz — all powered by Google's Gemini API.

**Live demo:** https://smartstudentai.onrender.com
*(Free hosting tier — the first request after a period of inactivity can
take up to ~50 seconds to wake up.)*

## Features

- **Upload** — add one or more PDFs to a conversation.
- **Summarize** — reads through the material a few pages at a time
  (roughly 8-10 per section), with Next/Back navigation. Already-read
  sections are cached, so revisiting them doesn't cost extra API usage.
- **Ask a question** — answers use the uploaded material as context, but
  aren't limited to it.
- **Generate a quiz** — five multiple-choice questions with click-to-answer
  options (correct/incorrect shown instantly).
- **History** — past conversations are saved and can be resumed at any
  time, continuing exactly where you left off. No login required —
  conversations are tied to an anonymous, cookie-based session.

## Tech stack

- **Backend:** Python, FastAPI, Google Gemini API (`google-genai`)
- **Database:** PostgreSQL
- **Frontend:** Plain HTML/CSS/JavaScript (no framework)
- **Hosting:** Render (app) + Neon (database)

## Project structure

```
backend/
├── main.py       # FastAPI app and routes
├── ai.py         # Gemini client + friendly error handling
├── database.py   # PostgreSQL connection
├── session.py    # Anonymous session/ownership checks
├── chunking.py   # Splits a document into study-sized sections
├── models.py     # Pydantic request/response models
└── static/       # Frontend (index.html, style.css, app.js)
```

## Running it locally

1. Install dependencies:
   ```
   pip install -r backend/requirements.txt
   ```
2. Create a PostgreSQL database with three tables: `conversations`,
   `documents`, and `results` (see the schema in the project notes, or ask
   for the `CREATE TABLE` statements).
3. Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   ```
4. Run the server from the `backend/` folder:
   ```
   uvicorn main:app --reload
   ```
5. Open `http://127.0.0.1:8000` in your browser.
