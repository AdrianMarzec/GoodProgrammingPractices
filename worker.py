#worker.py
import json
import os
import time
import uuid
from typing import Any, Dict
import pika
import requests #HTTP requests do Serwisu A
from detector_yolo import detect_people #liczenie ludzi w innym pliku jest

# config
RABBIT_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBIT_USER = os.getenv("RABBITMQ_USER", "admin")
RABBIT_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "1234")
TASK_QUEUE = os.getenv("TASK_QUEUE", "tasks") #kolejka z taskami na rabbit

SERVICE_A_URL = os.getenv("SERVICE_A_URL", "http://localhost:6767") #endpoint serwisu A
SAVE_IMG_PATH = os.getenv("SAVE_IMG_PATH", "")



def process_message(channel, method, properties, body):
    try:
        payload = json.loads(body.decode("utf-8"))
        task_id = payload["task_id"] #wyciąga id, url, czy zapis i gdzie
        source = payload["source"]
        save_img = bool(payload.get("save_img", False))
        save_path = payload.get("save_path") or SAVE_IMG_PATH

        if save_path:
            os.makedirs(save_path, exist_ok=True)

        result_file = os.path.join(save_path, f"{task_id}.json") if save_path else f"{task_id}.json"

        #Ostrożność na wypadek upadnięcia serwisu A - Yolo (i zapis jpg) tylko raz
        if os.path.exists(result_file):
            try:
                with open(result_file, "r") as f:
                    cached = json.load(f)
                    result = cached["result"]
            except Exception:
                os.remove(result_file)
                raise
        else:
            result = detect_people(source, save_img, save_path) #wywołanie YOLO
            with open(result_file, "w") as f:
                json.dump(
                    {"result": result, "source": source},
                    f
                )

        resp = requests.post(
            f"{SERVICE_A_URL}/tasks/{task_id}/result",
                    json={
                        "result": result,
                        "status": "done",
                        "source": source
                    },
                    timeout=5
                )

        resp.raise_for_status()  #jeśli coś pójdzie nie tak z łączeniem do A

        channel.basic_ack(delivery_tag=method.delivery_tag) #potwierdzenie przetworzenia
    except Exception as e:
        #jeśli błąd to mechanizm ponowienia taska w kolejce, bez utraty danych
        #retry + requeue gwarantuje odporność na chwilowe błędy Serwisu A lub sieci
        print("Worker error:", e, flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

#KONSUMENT RabbitMQ
"""
    1. Łączy się z RabbitMQ z użyciem credentials
    2. Deklaruje kolejki TASK_QUEUE
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