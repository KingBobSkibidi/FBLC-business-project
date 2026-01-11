from psycopg.rows import dict_row
import psycopg

DB_CONFIG = {
    "dbname": "locally",
    "user": "postgres",
    "password": "Bai12345!", 
    "host": "localhost",
    "port": 5432
}

def get_db_connection():
    conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row)
    return conn
