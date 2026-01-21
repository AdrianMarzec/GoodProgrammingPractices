#service_a.py
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional
import pytz #strefy czasowe
from flask import Flask, jsonify, request #API Serwisu A

# config
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
    
    #Pobiera wszystkie taski z bazy
    def get_all_tasks(self) -> list[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


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

#Zapisuje wynik taska
@app.route("/tasks/<task_id>/result", methods=["POST"])
def update_task_result(task_id: str):
    data = request.get_json(force=True, silent=True) or {}

    if "result" not in data:
        return jsonify({"error": "result is required"}), 400

    status = data.get("status", "done")
    result = int(data["result"])

    task = repo.get_task(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404

    repo.update_result(task_id, result, status=status)
    return jsonify({"task_id": task_id, "status": status}), 200

#Pobiera wszystkie taski z bazy
@app.route("/tasks", methods=["GET"])
def list_tasks():
    tasks = repo.get_all_tasks()
    return jsonify(tasks), 200


#URUCHAMIA SERWIS
if __name__ == "__main__":
    #Flask API Serwis A
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "6767")), debug=False)
