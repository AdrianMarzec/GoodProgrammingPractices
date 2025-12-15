# consumer.py
import sqlite3
import time
from datetime import datetime

DB_NAME = "tasks.db"

CHECK_INTERVAL = 5
WORK_TIME = 30

def get_task():
    conn = sqlite3.connect(DB_NAME)
    conn.isolation_level = None  # ręczne transakcje
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT id FROM tasks
            WHERE status = 'pending'
            ORDER BY id
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            conn.rollback()
            return None

        task_id = row[0]

        cursor.execute("""
            UPDATE tasks
            SET status = 'in_progress'
            WHERE id = ?
        """, (task_id,))

        conn.commit()
        print(f"[{datetime.now()}] Konsument pobrał zadanie {task_id}")
        return task_id

    except sqlite3.OperationalError:
        conn.rollback()
        return None

    finally:
        conn.close()

def finish_task(task_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            UPDATE tasks
            SET status = 'done'
            WHERE id = ?
        """, (task_id,))
    print(f"Zadanie {task_id} zakończone")

def consumer_loop():
    print("Konsument wystartował...")

    while True:
        task_id = get_task()

        if task_id is None:
            print("Brak zadań. Czekam...")
            time.sleep(CHECK_INTERVAL)
            continue

        print(f"Pracuję nad zadaniem {task_id} ({WORK_TIME}s)")
        time.sleep(WORK_TIME)
        finish_task(task_id)

if __name__ == "__main__":
    consumer_loop()
