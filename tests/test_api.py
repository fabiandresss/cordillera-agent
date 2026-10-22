"""API HTTP (FastAPI) sobre el agente. Sin red ni LLM."""
import pytest
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def client(world):
    with TestClient(create_app()) as c:
        yield c


def test_health_y_overview_inicial(client):
    assert client.get("/api/health").json()["ok"] is True
    ov = client.get("/api/overview").json()
    assert len(ov["fleet"]) == 5 and len(ov["orders"]) == 25
    assert ov["kpis"]["trucks_ok"] == 5 and ov["kpis"]["pending"] == 25
    assert ov["clock"]["hm"] == "08:00"


def test_flujo_de_eventos(client):
    r = client.post("/api/events", json={"text": "Inicio de jornada"}).json()
    assert r["result"]["outcome"] == "ok" and r["overview"]["kpis"]["notifications"] == 25
    assert sum(len(x["stops"]) for x in r["overview"]["routes"]) == 25

    r = client.post("/api/events", json={"text": "A las 11:00 el camión 3 se averió"}).json()
    ov = r["overview"]
    assert r["result"]["classification"]["tipo"] == "averia"
    assert next(t for t in ov["fleet"] if t["id"] == 3)["status"] == "averiado"
    assert ov["kpis"]["trucks_ok"] == 4 and ov["kpis"]["replans"] == 1
    assert ov["clock"]["hm"] == "11:00" and len(ov["history"]) == 2
    assert ov["outbox"] and ov["incidents"][0]["type"] == "averia"
    assert all(s["truck_id"] != 3 for s in ov["orders"] if s["status"] == "asignado")


def test_ultimo_razonamiento_persiste_en_overview(client):
    client.post("/api/events", json={"text": "Inicio de jornada"})
    last = client.get("/api/overview").json()["last_result"]
    assert last["event"] == "Inicio de jornada" and last["log"]


def test_evento_ambiguo_pide_datos(client):
    r = client.post("/api/events", json={"text": "Se averió un camión"}).json()["result"]
    assert r["outcome"] == "needs_info" and r["needs_info"]


def test_validacion_de_entrada(client):
    assert client.post("/api/events", json={"text": " "}).status_code == 422
    assert client.post("/api/events", json={}).status_code == 422
    assert client.post("/api/provider", json={"provider": "gpt"}).status_code == 422


def test_cambio_de_proveedor_y_chat_sin_llm(client):
    r = client.post("/api/provider", json={"provider": "groq"}).json()
    assert r["overview"]["provider"] == "groq" and "GROQ_API_KEY" in (r["warning"] or "")
    client.post("/api/provider", json={"provider": "rules"})
    assert client.post("/api/chat", json={"question": "¿Qué camiones hay?"}).status_code == 409


def test_busqueda_semantica(client):
    hits = client.get("/api/memory/search", params={"q": "camión no arranca batería descargada"}).json()
    assert hits and hits[0]["metadata"]["type"] == "averia"
    assert client.get("/api/memory/search", params={"q": "a"}).status_code == 422


def test_reset_reinicia_jornada(client):
    client.post("/api/events", json={"text": "Inicio de jornada"})
    ov = client.post("/api/reset").json()
    assert ov["kpis"]["pending"] == 25 and ov["kpis"]["notifications"] == 0 and ov["history"] == []
    assert ov["last_result"] is None
