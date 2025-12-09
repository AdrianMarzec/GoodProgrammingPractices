# consumer.py
import csv
import time
import os
from datetime import datetime

FILE_NAME = "tasks.csv"

CHECK_INTERVAL = 5
WORK_TIME = 30

def read_tasks():
    tasks = []
    with open(FILE_NAME, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            tasks.append(row)
    return header, tasks

def write_tasks(header, tasks):
    with open(FILE_NAME, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(tasks)

def consume_task():
    if not os.path.isfile(FILE_NAME):
        print("Brak pliku kolejki...")
        return False

    header, tasks = read_tasks()

    # Znajdź pierwsze pending
    for i, task in enumerate(tasks):
        if task[1] == "pending":
            print(f"[{datetime.now()}] Konsument pobiera zadanie {i}")
            tasks[i][1] = "in_progress"
            write_tasks(header, tasks)
            return i  # index zadania

    return None

def finish_task(task_index):
    header, tasks = read_tasks()
    tasks[task_index][1] = "done"
    write_tasks(header, tasks)

def consumer_loop():
    print("Konsument wystartował...")

    while True:
        task_index = consume_task()

        if task_index is None:
            print("Brak zadań. Czekam...")
            time.sleep(CHECK_INTERVAL)
            continue

        print(f"Rozpoczynam pracę nad zadaniem {task_index} przez {WORK_TIME} sekund...")
        time.sleep(WORK_TIME)
        finish_task(task_index)
        print(f"Zadanie {task_index} zakończone.")

if __name__ == "__main__":
    consumer_loop()
