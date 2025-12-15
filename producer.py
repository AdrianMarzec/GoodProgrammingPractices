# producer.py
import sqlite3
from datetime import datetime

DB_NAME = "tasks.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

def add_task():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO tasks (created_at, status) VALUES (?, ?)",
            (datetime.now().isoformat(), "pending")
        )
    print("Dodano zadanie")

if __name__ == "__main__":
    init_db()
    add_task()
