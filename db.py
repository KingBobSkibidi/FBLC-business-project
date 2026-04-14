# handles database connection for Locally 

# imports statements
import os

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

# create and return database connection
def get_db_connection():
    database_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRES_URL_NON_POOLING")
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

        conn = psycopg.connect(**connect_kwargs)
        return conn

    conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row) # connect to PostgreSQL, create database and format rows as dictionary
    return conn
