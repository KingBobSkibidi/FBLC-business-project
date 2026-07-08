import os

import psycopg
from psycopg.rows import dict_row


def get_db_connection():
    db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if db_url:
        return psycopg.connect(db_url, row_factory=dict_row)
    return psycopg.connect(
        dbname=os.getenv("PGDATABASE", "locally"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        row_factory=dict_row,
    )
