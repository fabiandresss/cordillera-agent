"""Herramientas de CONSULTA (solo lectura)."""
from .. import config, db, memory


def get_fleet_status() -> list[dict]:
    """Estado de la flota: patente, estado, capacidad, carga pendiente, zona actual y paradas por hacer."""
    out = []
    for t in db.rows("SELECT * FROM trucks ORDER BY id"):
        pend = db.rows(
            "SELECT a.order_id, o.weight_kg FROM assignments a JOIN orders o ON o.id=a.order_id "
            "WHERE a.truck_id=? AND a.status='planificado'", (t["id"],))
        out.append({
            "id": t["id"], "plate": t["plate"], "driver": t["driver"], "status": t["status"],
            "capacity_kg": t["capacity_kg"], "load_kg": sum(p["weight_kg"] for p in pend),
            "pending_stops": len(pend), "current_zone": current_zone(t["id"]),
        })
    return out


def current_zone(truck_id: int) -> str:
    r = db.one(
        "SELECT o.zone FROM assignments a JOIN orders o ON o.id=a.order_id "
        "WHERE a.truck_id=? AND a.status IN ('entregado','fallida') ORDER BY a.eta DESC LIMIT 1",
        (truck_id,))
    return r["zone"] if r else db.DEPOT_ZONE


def get_pending_orders(zone: str | None = None) -> list[dict]:
    """Pedidos pendientes o asignados aún no entregados; opcionalmente filtrados por zona."""
    sql = "SELECT * FROM orders WHERE status IN ('pendiente','asignado')"
    params: tuple = ()
    if zone:
        sql += " AND zone=?"
        params = (zone,)
    out = db.rows(sql + " ORDER BY window_end", params)
    for o in out:
        o["window"] = f"{db.hm(o['window_start'])}-{db.hm(o['window_end'])}"
    return out


def get_order(order_id: int) -> dict | None:
    """Datos de un pedido por su id."""
    return db.one("SELECT * FROM orders WHERE id=?", (order_id,))


def get_traffic(zone: str, hour: int) -> float:
    """Multiplicador de tiempo de viaje por tráfico en una zona y hora del día (1.0 = fluido)."""
    return db.traffic_multiplier(zone, hour * 60)


def get_client_profile(client_id: int) -> dict | None:
    """Perfil del cliente: nombre, nivel (VIP/normal), pedidos y entregas fallidas previas."""
    c = db.one("SELECT * FROM clients WHERE id=?", (client_id,))
    if not c:
        return None
    fails = db.one("SELECT COUNT(*) n FROM incidents WHERE client_id=? AND type='entrega_fallida'",
                   (client_id,))["n"]
    orders = db.one("SELECT COUNT(*) n FROM orders WHERE client_id=?", (client_id,))["n"]
    return {**c, "failed_deliveries": fails, "orders_today": orders}


def get_route(truck_id: int) -> list[dict]:
    """Ruta planificada de un camión, en orden de visita."""
    out = db.rows(
        "SELECT a.seq, a.order_id, a.eta, a.status, o.zone, o.window_start, o.window_end, o.client_id "
        "FROM assignments a JOIN orders o ON o.id=a.order_id "
        "WHERE a.truck_id=? AND a.status IN ('planificado','entregado') ORDER BY a.seq", (truck_id,))
    for s in out:
        s["eta_hm"] = db.hm(s["eta"])
    return out


def search_past_incidents(query: str, k: int = 3) -> list[dict]:
    """Búsqueda semántica de incidentes pasados parecidos a la consulta, con su resolución."""
    return memory.search_incidents(query, k=k)


def search_policies(query: str, k: int = 2) -> list[dict]:
    """Búsqueda semántica en las políticas operativas de la empresa."""
    return memory.search_policies(query, k=k)


def operational_trucks(now: int) -> list[dict]:
    """Camiones operativos listos para planificar (formato del planificador)."""
    out = []
    for t in db.rows("SELECT * FROM trucks WHERE status!='averiado' ORDER BY id"):
        out.append({"id": t["id"], "remaining_kg": t["capacity_kg"],
                    "start_zone": current_zone(t["id"]), "shift_end": t["shift_end"],
                    "start_time": max(now, config.SHIFT_START)})
    return out


def open_orders() -> list[dict]:
    """Pedidos por entregar hoy (formato del planificador)."""
    return db.rows("SELECT * FROM orders WHERE status IN ('pendiente','asignado') ORDER BY id")


def client_tiers() -> dict[int, str]:
    return {c["id"]: c["tier"] for c in db.rows("SELECT id, tier FROM clients")}


def previous_plan() -> dict[int, dict]:
    """order_id -> {truck_id, eta} del plan vigente (para detectar cambios y dar estabilidad)."""
    return {r["order_id"]: {"truck_id": r["truck_id"], "eta": r["eta"]}
            for r in db.rows("SELECT order_id, truck_id, eta FROM assignments WHERE status='planificado'")}
