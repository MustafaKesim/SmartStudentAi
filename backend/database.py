"""
Database access: a single function that opens a connection to PostgreSQL.

We open a brand new connection per call (instead of sharing one global
connection) because FastAPI runs our (synchronous) route handlers in a
thread pool -- a single shared connection isn't safe to use from multiple
threads at once. At our scale, the cost of reconnecting each time is
negligible.
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        # Local WSL Postgres has no SSL set up ("prefer" falls back to plain
        # automatically), but Neon's pooler flatly rejects non-SSL
        # connections rather than negotiating down -- so in production we
        # set DB_SSLMODE=require as an extra environment variable.
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
    )
