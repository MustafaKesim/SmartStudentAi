"""
Identity and ownership: who is making this request (via an anonymous,
cookie-based session -- no login required), and which conversation/document
they're actually allowed to act on.

Every place that looks up a document by conversation_id also checks that the
conversation belongs to this owner_id. Without that check, someone could
edit their conversation_id cookie in the browser and read another person's
uploaded document.
"""

import secrets
from fastapi import Request, Response, HTTPException

from database import get_connection


def get_owner_id(request: Request, response: Response):
    req = request.cookies.get("session_id")
    if req is None:
        # secrets.token_hex gives an unguessable random id -- unlike a
        # simple counter, it can't be enumerated to find other sessions.
        req = secrets.token_hex(16)
        response.set_cookie("session_id", req, httponly=True)
    owner_id = req
    return owner_id


def get_current_document(request: Request, owner_id: str):
    """Find the most recently uploaded document in the current conversation,
    but only if that conversation actually belongs to this owner_id.
    Raises an error if there's no active conversation or no document yet."""
    conversation_id = request.cookies.get("conversation_id")
    if conversation_id is None:
        raise HTTPException(status_code=400, detail="Please upload a PDF first.")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT documents.id, documents.content
        FROM documents
        JOIN conversations ON conversations.id = documents.conversation_id
        WHERE documents.conversation_id = %s AND conversations.owner_id = %s
        ORDER BY documents.uploaded_at DESC LIMIT 1
        """,
        (conversation_id, owner_id),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=400, detail="Please upload a PDF first.")

    document_id, content = row
    return document_id, content
