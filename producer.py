# producer.py
import csv
import uuid
import time

FILE_PATH = "tasks.csv"


def add_task():
    task_id = str(uuid.uuid4())
    with open(FILE_PATH, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([task_id, "pending"])
    print(f"Added task {task_id}")


if __name__ == "__main__":
    print("Producer running...")
    for _ in range(100):
        add_task()
        time.sleep(0.01)
