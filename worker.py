#worker.py
import json
import os
import time
import uuid
from typing import Any, Dict
import pika
from detector_yolo import detect_people #liczenie ludzi w innym pliku jest

# config
RABBIT_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBIT_USER = os.getenv("RABBITMQ_USER", "admin")
RABBIT_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "1234")
TASK_QUEUE = os.getenv("TASK_QUEUE", "tasks") #kolejka z taskami na rabbit
RESULT_QUEUE = os.getenv("RESULT_QUEUE", "results") #kolejka z wynikami
SERVICE_A_URL = os.getenv("SERVICE_A_URL", "http://localhost:6767") #endpoint serwisu A
SAVE_IMG_PATH = os.getenv("SAVE_IMG_PATH", "")


def publish_result(channel, message: Dict[str, Any]) -> None:
    channel.basic_publish(
        exchange="",
        routing_key=RESULT_QUEUE, #wysyła do koeljki z wynikami
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent
            content_type="application/json",
            correlation_id=str(uuid.uuid4()),
        ),
    )


def process_message(channel, method, properties, body):
    try:
        payload = json.loads(body.decode("utf-8"))
        task_id = payload["task_id"] #wyciąga id, url, czy zapis i gdzie
        source = payload["source"]
        save_img = bool(payload.get("save_img", False))
        save_path = payload.get("save_path", SAVE_IMG_PATH)

        # actual detection
        result = detect_people(source, save_img, save_path) #wywołanie YOLO

        publish_result(channel, {"task_id": task_id, "result": result, "status": "done"}) #wynik na kolejkę wynikową
        channel.basic_ack(delivery_tag=method.delivery_tag) #potwierdzenie przetworzenia
    except Exception:
        #jeśli błąd to mechanizm ponowienia taska w kolejce, bez utraty danych
        #retry + requeue gwarantuje odporność na chwilowe błędy Serwisu A lub sieci
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

#KONSUMENT RabbitMQ
"""
    1. Łączy się z RabbitMQ z użyciem credentials
    2. Deklaruje kolejki TASK_QUEUE i RESULT_QUEUE
    3. Ustawia prefetch_count=1 (jeden task na workera)
    4. Nasłuchuje TASK_QUEUE i wywołuje process_message dla każdego taska
    5. W przypadku braku połączenia → retry co 2 sekundy
"""
def run_consumer():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, credentials=credentials)

    # connect until rabbit is reachable
    while True:
        try:
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=TASK_QUEUE, durable=True) # False czyści przy restarcie
            channel.queue_declare(queue=RESULT_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1) #jeden task na workera
            channel.basic_consume(queue=TASK_QUEUE, on_message_callback=process_message)
            channel.start_consuming()
        except Exception:
            #jeśli RabbitMQ chwilowo niedostępny, próbuj ponownie po 2 sekundach
            time.sleep(2)
            continue

#rozpoczyna działanie workera
if __name__ == "__main__":
    run_consumer()


"""
Jeden worker dostaje jeden task na raz, co zapobiega przeciążeniu i pozwala równomiernie rozłożyć pracę.

Ack/Nack + requeue daje odporność na chwilowe błędy (Service A nie działa, Cloudflare przerwało połączenie)

Persistent message robi że taski nie zginą, nawet jeśli RabbitMQ się zrestartuje

Reconnect loop - worker zawsze próbuje połączyć się z RabbitMQ, nie wymaga restartu kontenera

Worker odpowiada tylko za detekcję i publikację wyników, nie zna logiki API.
"""