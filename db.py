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

_schema_init_lock = Lock()
_schema_initialized = False
_required_tables = ("users", "businesses", "saved_businesses", "ratings")


def _connect_from_env():
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

        return psycopg.connect(**connect_kwargs)

    pg_host = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
    pg_user = os.getenv("PGUSER") or os.getenv("POSTGRES_USER")
    if pg_host and pg_user:
        return psycopg.connect(
            dbname=os.getenv("PGDATABASE") or os.getenv("POSTGRES_DATABASE") or "postgres",
            user=pg_user,
            password=os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD"),
            host=pg_host,
            port=int(os.getenv("PGPORT") or os.getenv("POSTGRES_PORT") or "5432"),
            sslmode=os.getenv("PGSSLMODE", "require"),
            prepare_threshold=None,
            row_factory=dict_row,
        )

    return None


def _initialize_schema_if_needed(conn):
    global _schema_initialized
    if _schema_initialized:
        return

    with _schema_init_lock:
        if _schema_initialized:
            return

        with conn.cursor() as cur:
            all_tables_exist = True
            for table_name in _required_tables:
                cur.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table_name}",))
                row = cur.fetchone()
                if row["table_name"] is None:
                    all_tables_exist = False
                    break

            if not all_tables_exist:
                schema_path = Path(__file__).resolve().parent / "locally_db.sql"
                sql_script = schema_path.read_text(encoding="utf-8")
                cur.execute(sql_script)
                conn.commit()

            _schema_initialized = True


# create and return database connection
def get_db_connection():
    conn = _connect_from_env()
    if conn is None:
        conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row) # connect to PostgreSQL, create database and format rows as dictionary
    _initialize_schema_if_needed(conn)
    return conn
