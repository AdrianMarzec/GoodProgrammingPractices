# main.py
import subprocess
import time
import sqlite3
import os

PRODUCER = "producer.py"
CONSUMER = "consumer.py"
DB_NAME = "tasks.db"

NUM_TASKS = 100
NUM_CONSUMERS = 5

def create_tasks():
    print(f"Tworzę {NUM_TASKS} zadań...")
    for _ in range(NUM_TASKS):
        subprocess.run(["python", PRODUCER])

def start_consumers():
    print(f"Uruchamiam {NUM_CONSUMERS} konsumentów...\n")
    processes = []

    for _ in range(NUM_CONSUMERS):
        p = subprocess.Popen(["python", CONSUMER])
        processes.append(p)
        time.sleep(0.5)

    return processes

def wait_for_completion():
    print("\nOczekiwanie aż wszystkie zadania będą done...")

    while True:
        if not os.path.isfile(DB_NAME):
            time.sleep(2)
            continue

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    SUM(status = 'pending'),
                    SUM(status = 'in_progress'),
                    SUM(status = 'done')
                FROM tasks
            """)
            pending, in_progress, done = cursor.fetchone()

        pending = pending or 0
        in_progress = in_progress or 0
        done = done or 0

        print(f"pending={pending}, in_progress={in_progress}, done={done}")

        if pending == 0 and in_progress == 0:
            print("Wszystkie zadania zakończone!")
            break

        time.sleep(5)

def stop_consumers(processes):
    print("Zatrzymuję konsumentów...")
    for p in processes:
        p.terminate()
    print("Konsumenci zatrzymani.")

if __name__ == "__main__":
    create_tasks()
    consumers = start_consumers()
    wait_for_completion()
    stop_consumers(consumers)
