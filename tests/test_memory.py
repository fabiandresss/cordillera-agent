from src import memory
from src.tools import write


def test_indexa_incidentes_y_politicas(world):
    r = memory.index_all()
    assert r["incidentes"] == 15 and r["politicas"] > 0
    assert memory.index_all() == {}          # idempotente


def test_recupera_incidente_parecido(world):
    memory.index_all()
    hits = memory.search_incidents("camión no arranca batería descargada", incident_type="averia")
    assert hits and hits[0]["metadata"]["strategy"] == "reasignar_a_mayor_capacidad"


def test_incidente_nuevo_se_vuelve_recuperable(world):
    memory.index_all()
    write.log_incident("averia", "Se rompió la correa del alternador del camión", "Grúa y reasignación",
                       "reasignar_a_mayor_capacidad", truck_id=4)
    hits = memory.search_incidents("correa del alternador roto", threshold=0.1)
    assert any("alternador" in h["text"] for h in hits)


def test_politicas_recuperables(world):
    memory.index_all()
    hits = memory.search_policies("avería de un camión reasignar pedidos", threshold=0.1)
    assert hits and hits[0]["metadata"]["source"].startswith("02")


def test_umbral_filtra_ruido(world):
    memory.index_all()
    assert memory.search_incidents("receta de pastel de chocolate", threshold=0.6) == []


def test_memoria_caida_no_rompe(world, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("ollama caído")
    monkeypatch.setattr(memory, "_store", boom)
    assert memory.search_incidents("lo que sea") == []
