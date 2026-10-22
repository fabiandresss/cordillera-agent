from src import db


def test_datos_semilla(world):
    assert db.one("SELECT COUNT(*) n FROM trucks")["n"] == 5
    assert db.one("SELECT COUNT(*) n FROM orders")["n"] == 25
    assert db.one("SELECT COUNT(*) n FROM clients WHERE tier='VIP'")["n"] == 3
    assert db.one("SELECT COUNT(*) n FROM incidents")["n"] == 15


def test_ningun_pedido_excede_el_camion_mayor(world):
    max_cap = db.one("SELECT MAX(capacity_kg) m FROM trucks")["m"]
    assert db.one("SELECT MAX(weight_kg) m FROM orders")["m"] <= max_cap


def test_seed_es_reproducible(world):
    from tests.conftest import load_seed
    a = db.rows("SELECT * FROM orders")
    load_seed().build()
    assert db.rows("SELECT * FROM orders") == a


def test_trafico_y_viaje(world):
    assert db.traffic_multiplier("Centro", 8 * 60) > db.traffic_multiplier("Centro", 12 * 60)
    assert db.travel_minutes("Industrial", "Centro", 12 * 60) < db.travel_minutes("Industrial", "Sur", 12 * 60)
