import pytest

from src.tools import reasoning


@pytest.mark.parametrize("texto,tipo", [
    ("El camión 3 se averió", "averia"),
    ("Se pinchó una rueda del camión 2", "averia"),
    ("Cliente ausente en el pedido 8", "entrega_fallida"),
    ("Rechazaron el pedido 4 por embalaje", "entrega_fallida"),
    ("El cliente VIP necesita urgente el pedido 14", "vip_urgente"),
    ("Inicio de jornada", "nuevo_dia"),
    ("Hoy llueve mucho", "otro"),
])
def test_clasificador_por_reglas(world, texto, tipo):
    assert reasoning.classify_event(texto)["tipo"] == tipo


def test_extrae_entidades_y_horas(world):
    e = reasoning.extract_entities("A las 11:30 el cliente 2 pide el pedido 14 antes de las 12:00")
    assert (e["client_id"], e["order_id"], e["event_minute"], e["deadline"]) == (2, 14, 11 * 60 + 30, 12 * 60)


def test_id_inexistente_se_descarta(world):
    c = reasoning.classify_event("El camión 77 se averió")
    assert c["truck_id"] is None and c["invalid_truck"] == 77 and c["missing_info"]


def _fake_llm(monkeypatch, tipo):
    class Fake:
        def with_structured_output(self, schema):
            return self

        def invoke(self, _):
            return reasoning.EventClassification(tipo=tipo, resumen="x")

    monkeypatch.setattr(reasoning, "get_llm", lambda: Fake())


def test_reglas_prevalecen_sobre_llm_equivocado(world, monkeypatch):
    _fake_llm(monkeypatch, "otro")
    c = reasoning.classify_event("El camión 3 se averió")
    assert c["tipo"] == "averia" and "prevalecieron" in c["source"]


def test_nuevo_dia_propuesto_solo_por_llm_se_rechaza(world, monkeypatch):
    # Caso real observado con qwen2.5:1.5b: confundió una entrega fallida con 'nuevo_dia'.
    _fake_llm(monkeypatch, "nuevo_dia")
    assert reasoning.classify_event("Hoy hace calor")["tipo"] == "otro"
    assert reasoning.classify_event("Cliente ausente en el pedido 8")["tipo"] == "entrega_fallida"


def test_llm_aporta_cuando_las_reglas_no_matchean(world, monkeypatch):
    _fake_llm(monkeypatch, "averia")
    c = reasoning.classify_event("El vehículo 3 quedó botado en la carretera")
    assert c["tipo"] == "averia" and c["source"] == "llm"


def test_llm_que_falla_cae_a_reglas(world, monkeypatch):
    class Boom:
        def with_structured_output(self, schema):
            raise RuntimeError("sin red")

    monkeypatch.setattr(reasoning, "get_llm", lambda: Boom())
    assert reasoning.classify_event("El camión 3 se averió")["tipo"] == "averia"
