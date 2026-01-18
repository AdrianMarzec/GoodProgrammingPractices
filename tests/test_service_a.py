#test_service_a.py
import importlib


def test_create_and_get_task(tmp_path, monkeypatch):
    #tymczasowy plik bazy danych SQLite (unikalne dla testu)
    db_path = tmp_path / "results.db" # temp db file
    monkeypatch.setenv("RESULTS_DB_PATH", str(db_path)) # settest db path by service_a używał tej testowej bazy

    #Przeładowanie modułu service_a, aby wczytał nową ścieżkę do testowej bazy
    service_a = importlib.import_module("service_a")
    importlib.reload(service_a)

    #klient Flask do symulowania żądań HTTP
    app = service_a.app
    client = app.test_client()

    #nowy task (POST /tasks)
    task_payload = {"task_id": "test-task", "source": "http://example.com/img.jpg"}
    create_resp = client.post("/tasks", json=task_payload)
    assert create_resp.status_code == 201 #CZY DODANY POPRAWNIE

    #status taska (GET /tasks/<task_id>)
    status_resp = client.get("/tasks/test-task")
    assert status_resp.status_code == 200
    data = status_resp.get_json()
    #czy ID i status taska są zgodne z oczekiwaniami
    assert data["id"] == "test-task"
    assert data["status"] == "pending"


"""
Testy:
Czy Serwis A potrafi dodać taska do bazy.
Czy Serwis A potrafi pobrać taska po ID.
Test jest samowystarczalny, używa tymczasowej bazy
Nie zależy na RabbitMQ ani workerach, to jest test integracyjny tylko dla API i DB.
"""