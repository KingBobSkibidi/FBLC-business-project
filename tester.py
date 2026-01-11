import psycopg

DB_CONFIG = {
    "dbname": "locally",
    "user": "postgres",
    "password": "Bai12345!",
    "host": "localhost",
    "port": 5432
}

conn = psycopg.connect(**DB_CONFIG)
print("Connected!")
conn.close()