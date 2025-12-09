# producer.py
import csv
import os
from datetime import datetime

FILE_NAME = "tasks.csv"

def add_task():
    task = [
        str(datetime.now()),  # timestamp
        "pending"             # status
    ]

    file_exists = os.path.isfile(FILE_NAME)

    with open(FILE_NAME, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["created_at", "status"])
        writer.writerow(task)

    print("Dodano zadanie:", task)

if __name__ == "__main__":
    add_task()
