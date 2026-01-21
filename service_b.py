#service_b.py
import json
import os
import uuid
from typing import Any, Dict
import pika #klient RabbitMQ
import requests #HTTP requests do Serwisu A
from flask import Flask, jsonify, request, render_template #API i demonstracja

RABBIT_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBIT_USER = os.getenv("RABBITMQ_USER", "admin")
RABBIT_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "1234")
TASK_QUEUE = os.getenv("TASK_QUEUE", "tasks") #nazwa kolejki zadań
SERVICE_A_URL = os.getenv("SERVICE_A_URL", "http://localhost:6767") #endpoint Serwisu A

app = Flask(__name__)

# Funkcja do wysyłania taska do RabbitMQ
def _publish_task(message: Dict[str, Any]) -> None:
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=TASK_QUEUE, durable=True) #połączenie synchroniczne
    channel.basic_publish(
        exchange="",
        routing_key=TASK_QUEUE, #wysyła do koeljki z taskami
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent, RabbitMQ zapisze na dysk, task nie zginie przy restarcie
            content_type="application/json",
            correlation_id=str(uuid.uuid4()), #Unikalne id wiadomości
        ),
    )
    connection.close()

#Rejestracja taska w Serwisie A
#Wysyła POST /tasks z task_id, URL i statusem pending
def _register_task_with_service_a(task_id: str, source: str) -> None:
    payload = {"task_id": task_id, "source": source, "status": "pending"}
    resp = requests.post(f"{SERVICE_A_URL}/tasks", json=payload, timeout=5)
    resp.raise_for_status() #wyrzuca wyjątek jeśli HTTP != 2xx


#Demonstracyjny html do testowania
@app.route("/", methods=["GET"])
def home():
    return render_template("testing_form.html")


@app.route("/status/<task_id>", methods=["GET"])
def proxy_status(task_id: str): #Endpoint. Pobiera status taska z Serwisu A
    try:
        resp = requests.get(f"{SERVICE_A_URL}/tasks/{task_id}", timeout=5)
        return jsonify(resp.json()), resp.status_code
    except Exception as exc:
        return jsonify({"error": f"could not fetch status: {exc}"}), 503


@app.route("/detect", methods=["POST"])
def enqueue_detection(): #Endpoint. Pobiera info z html (url, czy zapis i gdzie), rejestruje taska w Serwisie A i daje go na Rabbita
    data = request.get_json(force=True, silent=True) or {}
    source = data.get("url", "")
    if not (source.startswith("http://") or source.startswith("https://")):
        return jsonify({"error": "url must start with http:// or https://"}), 400
    save_img = bool(data.get("save_img", False))
    save_path = data.get("save_path", "")

    if not source:
        return jsonify({"error": "url is required"}), 400

    task_id = str(uuid.uuid4())
    
    #enqueue do RabbitMQ
    try:
        _publish_task(
            {"task_id": task_id, "source": source, "save_img": save_img, "save_path": save_path}
        )
    except Exception as exc:
        return jsonify({"error": f"could not enqueue task: {exc}"}), 503
    
    try:
        _register_task_with_service_a(task_id, source)
    except Exception as exc:
        return jsonify({"error": f"could not register task with service A: {exc}"}), 503

    return jsonify({"task_id": task_id}), 202

#Sprawdzenie statusu serwisu
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

#Uruchamia apke
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "6969")), debug=False)
