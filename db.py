# handles database connection for Locally 

# imports statements
import os
from pathlib import Path
from threading import Lock

from psycopg.rows import dict_row
import psycopg

# database connection settings
DB_CONFIG = {
    "dbname": "locally",
    "user": "postgres",
    "password": "Bai12345!", 
    "host": "localhost",
    "port": 5432
}

_schema_lock = Lock()
_schema_initialized = False


class DatabaseConnectionError(Exception):
    pass


def _connect():
    database_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRES_URL_NON_POOLING")
        or os.getenv("POSTGRES_PRISMA_URL")
    )

    if database_url:
        connect_kwargs = {
            "conninfo": database_url,
            "prepare_threshold": None,
            "row_factory": dict_row,
        }
        if os.getenv("PGSSLMODE"):
            connect_kwargs["sslmode"] = os.getenv("PGSSLMODE")
        elif os.getenv("VERCEL"):
            connect_kwargs["sslmode"] = "require"
        try:
            return psycopg.connect(**connect_kwargs)
        except psycopg.Error as error:
            raise DatabaseConnectionError(
                "Could not connect to hosted PostgreSQL. Check DATABASE_URL/POSTGRES_URL in Vercel env vars."
            ) from error

    # Support providers that expose host/user/password vars instead of a single URL.
    if os.getenv("PGHOST") and os.getenv("PGUSER"):
        try:
            return psycopg.connect(
                dbname=os.getenv("PGDATABASE", "postgres"),
                user=os.getenv("PGUSER"),
                password=os.getenv("PGPASSWORD"),
                host=os.getenv("PGHOST"),
                port=int(os.getenv("PGPORT", "5432")),
                sslmode=os.getenv("PGSSLMODE", "require"),
                prepare_threshold=None,
                row_factory=dict_row,
            )
        except psycopg.Error as error:
            raise DatabaseConnectionError(
                "Could not connect to PostgreSQL using PGHOST/PGUSER variables."
            ) from error

    # Support providers that expose POSTGRES_* host/user/password vars.
    if os.getenv("POSTGRES_HOST") and os.getenv("POSTGRES_USER"):
        try:
            return psycopg.connect(
                dbname=os.getenv("POSTGRES_DATABASE", "postgres"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                sslmode=os.getenv("PGSSLMODE", "require"),
                prepare_threshold=None,
                row_factory=dict_row,
            )
        except psycopg.Error as error:
            raise DatabaseConnectionError(
                "Could not connect to PostgreSQL using POSTGRES_HOST/POSTGRES_USER variables."
            ) from error

    try:
        return psycopg.connect(**DB_CONFIG, row_factory=dict_row)
    except psycopg.Error as error:
        raise DatabaseConnectionError(
            "Could not connect to local PostgreSQL. For Vercel, set DATABASE_URL or connect Vercel Postgres."
        ) from error


def _initialize_schema_if_needed(conn):
    global _schema_initialized
    if _schema_initialized:
        return

    with _schema_lock:
        if _schema_initialized:
            return

        schema_path = Path(__file__).resolve().parent / "locally_db.sql"
        sql_script = schema_path.read_text(encoding="utf-8")

        with conn.cursor() as cur:
            for statement in sql_script.split(";"):
                statement = statement.strip()
                if statement:
                    cur.execute(statement)
        conn.commit()
        _schema_initialized = True


# create and return database connection
def get_db_connection():
    conn = _connect()
    _initialize_schema_if_needed(conn)
    return conn
