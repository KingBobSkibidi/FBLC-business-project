# handles database connection for Locally

import os
from pathlib import Path
from threading import Lock

import psycopg
from psycopg.rows import dict_row


PROJECT_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PROJECT_ROOT / "locally_db.sql"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

_db_init_lock = Lock()
_db_initialized = False


class DatabaseConfigurationError(RuntimeError):
    """Raised when database environment variables are missing or invalid."""


class DatabaseConnectionError(RuntimeError):
    """Raised when the app cannot connect to PostgreSQL."""


def _build_connection_kwargs():
    conninfo = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRES_URL_NON_POOLING")
    )
    sslmode = os.getenv("PGSSLMODE") or os.getenv("DB_SSLMODE")

    if conninfo:
        kwargs = {
            "conninfo": conninfo,
            "prepare_threshold": None,
            "row_factory": dict_row,
        }
        if sslmode:
            kwargs["sslmode"] = sslmode
        elif os.getenv("VERCEL"):
            kwargs["sslmode"] = "require"
        return kwargs

    host = os.getenv("PGHOST") or os.getenv("DB_HOST") or "localhost"
    port = int(os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432")
    dbname = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or "locally"
    user = os.getenv("PGUSER") or os.getenv("DB_USER") or "postgres"
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD") or ""

    if os.getenv("VERCEL") and host in LOCAL_HOSTS:
        raise DatabaseConfigurationError(
            "No hosted PostgreSQL database is configured. Set DATABASE_URL or "
            "connect a Vercel Postgres database before deploying."
        )

    kwargs = {
        "dbname": dbname,
        "host": host,
        "port": port,
        "prepare_threshold": None,
        "row_factory": dict_row,
        "user": user,
    }
    if password:
        kwargs["password"] = password
    if sslmode:
        kwargs["sslmode"] = sslmode
    elif host not in LOCAL_HOSTS:
        kwargs["sslmode"] = "require"

    return kwargs


def _connect():
    try:
        return psycopg.connect(**_build_connection_kwargs())
    except psycopg.OperationalError as exc:
        raise DatabaseConnectionError(
            "Could not connect to PostgreSQL. Set DATABASE_URL (or the PGHOST/"
            "PGDATABASE/PGUSER/PGPASSWORD/PGPORT variables) and make sure the "
            "database is reachable."
        ) from exc


def _split_sql_statements(script):
    statements = []
    current = []
    in_string = False
    index = 0

    while index < len(script):
        char = script[index]

        if char == "'":
            current.append(char)
            if in_string and index + 1 < len(script) and script[index + 1] == "'":
                current.append(script[index + 1])
                index += 1
            else:
                in_string = not in_string
        elif char == ";" and not in_string:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)

        index += 1

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)

    return statements


def _initialize_database(connection):
    if not SCHEMA_PATH.exists():
        raise DatabaseConfigurationError(
            f"Database seed file not found at {SCHEMA_PATH}."
        )

    sql_script = SCHEMA_PATH.read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        for statement in _split_sql_statements(sql_script):
            cursor.execute(statement)
    connection.commit()


def get_db_connection():
    global _db_initialized

    connection = _connect()
    if _db_initialized:
        return connection

    with _db_init_lock:
        if _db_initialized:
            return connection

        try:
            _initialize_database(connection)
        except Exception:
            connection.close()
            raise

        _db_initialized = True

    return connection
