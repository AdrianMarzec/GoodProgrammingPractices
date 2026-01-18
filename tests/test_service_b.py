#test_service_b.py
import importlib


def test_detect_enqueue(monkeypatch):
    #Słownik do przechwycenia danych, które normalnie poszłyby do RabbitMQ i Serwisu A
    captured = {}

    #Zastąpienie funkcji rejestrującej taska w Serwisie A
    #zamiast robić prawdziwy POST, zapisanie danych w captured
    def fake_register(task_id, source):
        captured["registered"] = (task_id, source)

    #Zastąpienie funkcji publikującej taska do RabbitMQ
    #zapis payload w captured
    def fake_publish(message):
        captured["published"] = message

    #Import modułu z serwisem B i podmianka na funkcje do testów
    service_b = importlib.import_module("service_b")
    monkeypatch.setattr(service_b, "_register_task_with_service_a", fake_register)
    monkeypatch.setattr(service_b, "_publish_task", fake_publish)

    #klient Flask do symulowania żądań HTTP
    app = service_b.app
    client = app.test_client()

    #Wywołanie endpointu /detect z przykładowym URL
    resp = client.post("/detect", json={"url": "http://example.com/test.jpg"})
    assert resp.status_code == 202 #czy odpowiedź HTTP jest poprawna
    task_id = resp.get_json()["task_id"]
    #Czy task został "zarejestrowany" w Serwisie A
    assert captured["registered"][0] == task_id
    #Czy task został "opublikowany" do RabbitMQ
    assert captured["published"]["task_id"] == task_id
    assert captured["published"]["source"] == "http://example.com/test.jpg"

"""
Testy:
Endpoint /detect przyjmuje URL i zwraca task_id
Czy task jest poprawnie "zarejestrowany" w Serwisie A
Czy task poprawnie wchodzi do RabbitMQ
Test nie wymaga faktycznego Serwisu A ani RabbitMQ, bo używa monkeypatch do podmiany funkcji
Sprawdza integralność task_id i przesyłanych danych.
"""