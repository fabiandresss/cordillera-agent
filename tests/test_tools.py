import json

from src import config, db
from src.tools import query, write


def test_asignar_sobre_capacidad_falla(world):
    r = write.assign_orders(1, [o["id"] for o in db.rows("SELECT id FROM orders")])  # camión de 800 kg
    assert r["ok"] is False and "capacidad" in r["error"]


def test_no_asigna_a_camion_averiado(world):
    write.set_truck_status(2, "averiado")
    assert write.assign_orders(2, [1])["ok"] is False


def test_asignar_ok_y_hoja_de_ruta(world):
    assert write.assign_orders(5, [1, 2], [500, 520])["ok"]
    path = write.write_route_sheet(5)
    text = open(path, encoding="utf-8").read()
    assert "Camión 5" in text and "| 1 | 1 |" in text
    assert db.one("SELECT status FROM orders WHERE id=1")["status"] == "asignado"


def test_reprogramar_e_intentos(world):
    assert write.register_failed_delivery(5) == 1
    assert write.register_failed_delivery(5) == 2
    o = write.reschedule_order(5, 540, 720, same_day=False)
    assert o["status"] == "reprogramado"


def test_notificar_cliente_escribe_outbox(world):
    write.notify_client(2, "Hola", 14)
    line = (config.output_dir() / "outbox.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    assert json.loads(line)["client_id"] == 2


def test_prioridad_con_hora_limite(world):
    o = write.set_order_priority(14, 4, 12 * 60)
    assert o["priority"] == 4 and o["window_end"] == 720


def test_avanzar_reloj_marca_entregados(world):
    write.assign_orders(5, [1, 2], [500, 900])
    done = write.advance_clock(600)
    assert done == [1] and db.one("SELECT status FROM orders WHERE id=2")["status"] == "asignado"


def test_consultas(world):
    assert len(query.get_fleet_status()) == 5
    assert query.get_client_profile(2)["tier"] == "VIP"
    assert query.get_client_profile(999) is None
    assert query.get_traffic("Centro", 8) > 1.0
    assert all(o["zone"] == "Sur" for o in query.get_pending_orders("Sur"))
