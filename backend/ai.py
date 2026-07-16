"""
Gemini client and a wrapper around it that turns known API errors (rate
limit hit, service overloaded) into clear, friendly HTTP errors -- so the
frontend can show the student a helpful message instead of a raw crash.
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from fastapi import HTTPException

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


def generate_content(**kwargs):
    """Calls Gemini and turns known API errors into a clear, friendly
    HTTPException instead of letting a raw 500 reach the browser."""
    try:
        return client.models.generate_content(**kwargs)
    except genai_errors.APIError as e:
        # 429 = rate limit, resets after about a minute. Anything else
        # (e.g. 503) means Gemini's own servers are temporarily overloaded.
        if e.code == 429:
            raise HTTPException(
                status_code=429,
                detail="You've hit Gemini's rate limit. Please wait about a minute and try again.",
            )
        raise HTTPException(
            status_code=503,
            detail="The AI service is currently busy or unavailable. Please try again in a moment.",
        )
