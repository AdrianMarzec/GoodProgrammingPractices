# consumer.py
import csv
import time
import os
from datetime import datetime

FILE_PATH = "tasks.csv"
LOCK_FILE = "tasks.lock"


def lock():
    while os.path.exists(LOCK_FILE):
        time.sleep(0.1)
    open(LOCK_FILE, "w").close()


def unlock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def read_tasks():
    tasks = []
    try:
        with open(FILE_PATH, mode="r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    tasks.append(row)
    except FileNotFoundError:
        pass
    return tasks


def write_tasks(tasks):
    with open(FILE_PATH, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(tasks)


def process_task(task_id):
    print(f"[{datetime.now()}] Starting task {task_id}")
    time.sleep(30)
    print(f"[{datetime.now()}] Finished task {task_id}")


if __name__ == "__main__":
    print("Consumer started...")

    while True:
        lock()
        tasks = read_tasks()

        target_index = None
        for i, (tid, status) in enumerate(tasks):
            if status == "pending":
                target_index = i
                tasks[i][1] = "in_progress"
                write_tasks(tasks)
                break

        unlock()

        if target_index is None:
            time.sleep(5)
            continue

        task_id = tasks[target_index][0]
        process_task(task_id)

        lock()
        tasks = read_tasks()
        for j, (tid, status) in enumerate(tasks):
            if tid == task_id:
                tasks[j][1] = "done"
        write_tasks(tasks)
        unlock()
import csv
import time
from datetime import datetime

FILE_PATH = "tasks.csv"


def read_tasks():
    tasks = []
    try:
        with open(FILE_PATH, mode="r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    tasks.append(row)
    except FileNotFoundError:
        pass
    return tasks


def write_tasks(tasks):
    with open(FILE_PATH, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(tasks)


def process_task(task_id):
    print(f"[{datetime.now()}] Starting task {task_id}")
    time.sleep(30)  # simulate work
    print(f"[{datetime.now()}] Finished task {task_id}")


if __name__ == "__main__":
    print("Consumer started...")

    while True:
        tasks = read_tasks()
        updated = False

        for i, (task_id, status) in enumerate(tasks):
            if status == "pending":
                # mark as in progress
                tasks[i][1] = "in_progress"
                write_tasks(tasks)

                # execute work
                process_task(task_id)

                # mark as done
                tasks = read_tasks()
                for j, (tid, st) in enumerate(tasks):
                    if tid == task_id:
                        tasks[j][1] = "done"
                write_tasks(tasks)

                updated = True
                break

        if not updated:
            time.sleep(5)  # wait before checking again
