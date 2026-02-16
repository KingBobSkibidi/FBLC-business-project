# handles database connection for Locally 

# imports statements
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
    conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row) # connect to PostgreSQL, create database and format rows as dictionary
    return conn
