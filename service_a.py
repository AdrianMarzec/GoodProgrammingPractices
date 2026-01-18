#service_a.py
import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional
import pika
import pytz #strefy czasowe
from flask import Flask, jsonify, request #API Serwisu A

# config
RABBIT_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBIT_USER = os.getenv("RABBITMQ_USER", "admin")
RABBIT_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "1234")
RESULT_QUEUE = os.getenv("RESULT_QUEUE", "results") #kolejka z wynikami z workerów
DB_PATH = os.getenv("RESULTS_DB_PATH", "results.db") #plik sqlite
TZ = pytz.timezone(os.getenv("TZ", "UTC")) #strefa czasowa do timestampów


#czas w ISO
def utcnow_iso() -> str:
    return datetime.now(TZ).isoformat()


#Repozytorium/baza danych do przechowywania statusów tasków i wyników
class ResultRepository:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    #Tworzy tabelę jeśli nie istnieje
    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                result INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    #Dodanie lub aktualizacja taska jeśli już istnieje
    def upsert_task(self, task_id: str, source: str, status: str = "pending", result: Optional[int] = None) -> None:
        now = utcnow_iso()
        self.conn.execute(
            """
            INSERT INTO tasks (id, source, status, result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,
                result=excluded.result,
                updated_at=excluded.updated_at
            """,
            (task_id, source, status, result, now, now),
        )
        self.conn.commit()

    #Aktualizacja wyniku taska
    def update_result(self, task_id: str, result: int, status: str = "done") -> None:
        now = utcnow_iso()
        self.conn.execute(
            """
            UPDATE tasks
            SET status = ?, result = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, result, now, task_id),
        )
        self.conn.commit()

    #Pobiera task jako słownik po task_id
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None

#Inicjalizacja Flask i repozytorium
app = Flask(__name__)
repo = ResultRepository(DB_PATH)

#Tworzy nowy task lub aktualizuje istniejący
@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(force=True, silent=True) or {}
    task_id = data.get("task_id") or data.get("id")
    source = data.get("source")
    status = data.get("status", "pending")
    result = data.get("result")

    if not source:
        return jsonify({"error": "source is required"}), 400
    if not task_id:
        return jsonify({"error": "task_id is required"}), 400

    repo.upsert_task(task_id, source, status=status, result=result)
    return jsonify({"task_id": task_id, "status": status}), 201

#Pobiera status taska po ID
@app.route("/tasks/<task_id>", methods=["GET"])
def task_status(task_id: str):
    task = repo.get_task(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)

#Sprawdza stan serwisu
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


#CALLBACK dla odbierania wyników z RabbitMQ
"""
    1. Dekoduje JSON z kolejki RESULT_QUEUE
    2. Aktualizuje wynik w DB
    3. ACK jeśli OK
    4. NACK+requeue jeśli błąd, żeby nie stracić taska
"""
def _result_callback(channel, method, properties, body):
    try:
        payload = json.loads(body.decode("utf-8"))
        task_id = payload["task_id"]
        result = int(payload["result"])
        status = payload.get("status", "done")
        repo.update_result(task_id, result, status=status) # if failed then exception
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        # retry mechanizm + requeue, odporność na chwilowe błędy (np. worker, sieć)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True) # change to false if u trash queue when testing


#Funkcja konsumenta wyników (uruchamiana w osobnym wątku)
"""
    1. Łączy się z RabbitMQ
    2. Deklaruje RESULT_QUEUE
    3. Ustawia prefetch_count=1
    4. Konsumuje wiadomości z kolejki, wywołując _result_callback
    5. Retry co 2s jeśli Rabbit niedostępny
"""
def start_result_consumer():
    # (re)connect until rabbit is reachable
    while True:
        try:
            credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
            params = pika.ConnectionParameters(
                host=RABBIT_HOST, port=RABBIT_PORT, credentials=credentials
            )
            connection = pika.BlockingConnection(params) # tcp connection
            channel = connection.channel()
            channel.queue_declare(queue=RESULT_QUEUE, durable=True) # change to false if u want to clear queue on restart (for tests :P)
            channel.basic_qos(prefetch_count=1) # send one unacked messg at a time
            channel.basic_consume(queue=RESULT_QUEUE, on_message_callback=_result_callback)
            channel.start_consuming() # mnom mnom mnom
        except Exception:
            time.sleep(2)
            continue

#URUCHAMIA SERWIS
if __name__ == "__main__":
    if os.getenv("ENABLE_RESULT_CONSUMER", "true").lower() == "true":
        consumer_thread = threading.Thread(target=start_result_consumer, daemon=True)
        consumer_thread.start() #uruchamia w tle konsumenta wyników

    #Flask API Serwis A
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "6767")), debug=False)
