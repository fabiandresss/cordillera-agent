"""Herramientas de ESCRITURA (modifican BD y generan archivos)."""
import json

from .. import config, db, memory


def _ts() -> str:
    return f"{config.JORNADA} {db.hm(db.get_now())}"


def advance_clock(now: int) -> list[int]:
    """Avanza el reloj simulado y marca como entregados los pedidos cuya ETA ya pasó."""
    now = max(now, db.get_now())
    db.set_now(now)
    done = db.rows("SELECT id, order_id FROM assignments WHERE status='planificado' AND eta<=?", (now,))
    for a in done:
        db.execute("UPDATE assignments SET status='entregado' WHERE id=?", (a["id"],))
        db.execute("UPDATE orders SET status='entregado' WHERE id=?", (a["order_id"],))
    return [a["order_id"] for a in done]


def cancel_planned_assignments():
    """Anula el plan vigente (las entregas futuras) antes de aplicar uno nuevo."""
    for a in db.rows("SELECT order_id FROM assignments WHERE status='planificado'"):
        db.execute("UPDATE orders SET status='pendiente' WHERE id=? AND status='asignado'", (a["order_id"],))
    db.execute("UPDATE assignments SET status='cancelada' WHERE status='planificado'")


def assign_orders(truck_id: int, order_ids: list[int], etas: list[int] | None = None) -> dict:
    """Asigna pedidos a un camión en el orden dado. Falla si excede la capacidad o el camión está averiado."""
    truck = db.one("SELECT * FROM trucks WHERE id=?", (truck_id,))
    if not truck:
        return {"ok": False, "error": f"camión {truck_id} no existe"}
    if truck["status"] == "averiado":
        return {"ok": False, "error": f"camión {truck_id} está averiado"}
    weights = {o: db.one("SELECT weight_kg FROM orders WHERE id=?", (o,)) for o in order_ids}
    if any(w is None for w in weights.values()):
        return {"ok": False, "error": "pedido inexistente en la lista"}
    kept = db.one(
        "SELECT COALESCE(SUM(o.weight_kg),0) w FROM assignments a JOIN orders o ON o.id=a.order_id "
        "WHERE a.truck_id=? AND a.status='planificado'", (truck_id,))["w"]
    total = kept + sum(w["weight_kg"] for w in weights.values())
    if total > truck["capacity_kg"]:
        return {"ok": False, "error": f"capacidad excedida: {total}kg > {truck['capacity_kg']}kg"}
    start = db.one("SELECT COALESCE(MAX(seq),0) s FROM assignments WHERE truck_id=? AND status='planificado'",
                   (truck_id,))["s"]
    for i, oid in enumerate(order_ids):
        eta = etas[i] if etas else 0
        db.execute("INSERT INTO assignments(order_id,truck_id,seq,eta,status) VALUES (?,?,?,?,'planificado')",
                   (oid, truck_id, start + i + 1, eta))
        db.execute("UPDATE orders SET status='asignado' WHERE id=?", (oid,))
    return {"ok": True, "truck_id": truck_id, "assigned": order_ids, "load_kg": total}


def write_route_sheet(truck_id: int) -> str:
    """Genera la hoja de ruta (Markdown) del camión en outputs/ y devuelve su ruta."""
    t = db.one("SELECT * FROM trucks WHERE id=?", (truck_id,))
    stops = db.rows(
        "SELECT a.seq, a.eta, o.id oid, o.zone, o.weight_kg, o.window_start, o.window_end, c.name, c.tier "
        "FROM assignments a JOIN orders o ON o.id=a.order_id JOIN clients c ON c.id=o.client_id "
        "WHERE a.truck_id=? AND a.status='planificado' ORDER BY a.seq", (truck_id,))
    lines = [f"# Hoja de ruta — Camión {truck_id} ({t['plate']})",
             f"Conductor: {t['driver']} · Capacidad: {t['capacity_kg']} kg · Estado: {t['status']}",
             f"Generada: {_ts()}", ""]
    if not stops:
        lines.append("_Sin entregas pendientes._")
    else:
        lines += ["| # | Pedido | Cliente | Zona | Peso | Ventana | ETA |", "|---|---|---|---|---|---|---|"]
        for s in stops:
            vip = " ⭐VIP" if s["tier"] == "VIP" else ""
            lines.append(f"| {s['seq']} | {s['oid']} | {s['name']}{vip} | {s['zone']} | {s['weight_kg']} kg | "
                         f"{db.hm(s['window_start'])}-{db.hm(s['window_end'])} | {db.hm(s['eta'])} |")
    path = config.output_dir() / f"hoja_ruta_camion_{truck_id}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def notify_client(client_id: int, message: str, order_id: int | None = None) -> str:
    """Envía (simulado) un aviso al cliente: se guarda en outputs/outbox.jsonl."""
    rec = {"ts": _ts(), "client_id": client_id, "order_id": order_id,
           "channel": "email (simulado)", "message": message}
    path = config.output_dir() / "outbox.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return str(path)


def notify_supervisor(summary: str, recommendation: str) -> str:
    """Escribe una nota de escalamiento para el supervisor humano."""
    rec = {"ts": _ts(), "summary": summary, "recommendation": recommendation}
    path = config.output_dir() / "escalamientos.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return str(path)


def set_truck_status(truck_id: int, status: str) -> dict:
    """Cambia el estado de un camión (disponible/averiado)."""
    db.execute("UPDATE trucks SET status=? WHERE id=?", (status, truck_id))
    return {"truck_id": truck_id, "status": status}


def set_order_priority(order_id: int, priority: int, deadline: int | None = None) -> dict:
    """Sube/baja la prioridad de un pedido y opcionalmente acorta su hora límite."""
    if deadline is not None:
        db.execute("UPDATE orders SET priority=?, window_end=MIN(window_end,?) WHERE id=?",
                   (priority, deadline, order_id))
        db.execute("UPDATE orders SET window_start=MIN(window_start, window_end) WHERE id=?", (order_id,))
    else:
        db.execute("UPDATE orders SET priority=? WHERE id=?", (priority, order_id))
    return db.one("SELECT * FROM orders WHERE id=?", (order_id,))


def register_failed_delivery(order_id: int) -> int:
    """Registra una entrega fallida: +1 intento y marca la asignación vigente como fallida."""
    db.execute("UPDATE orders SET attempts=attempts+1 WHERE id=?", (order_id,))
    db.execute("UPDATE assignments SET status='fallida' WHERE order_id=? AND status IN ('planificado','entregado')",
               (order_id,))
    return db.one("SELECT attempts FROM orders WHERE id=?", (order_id,))["attempts"]


def reschedule_order(order_id: int, new_window_start: int, new_window_end: int, same_day: bool) -> dict:
    """Reprograma un pedido: mismo día (vuelve a la cola) o día siguiente (queda reprogramado)."""
    status = "pendiente" if same_day else "reprogramado"
    db.execute("UPDATE orders SET window_start=?, window_end=?, status=? WHERE id=?",
               (new_window_start, new_window_end, status, order_id))
    return db.one("SELECT * FROM orders WHERE id=?", (order_id,))


def escalate_order(order_id: int):
    """Marca un pedido como fallido/escalado (no se vuelve a planificar solo)."""
    db.execute("UPDATE orders SET status='fallido' WHERE id=?", (order_id,))


def log_incident(type: str, description: str, resolution: str, strategy: str = "",
                 truck_id: int | None = None, order_id: int | None = None,
                 client_id: int | None = None) -> int:
    """Registra un incidente en SQLite y lo indexa en la memoria semántica (ChromaDB)."""
    iid = db.execute(
        "INSERT INTO incidents(ts,type,truck_id,order_id,client_id,description,resolution,strategy) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (_ts(), type, truck_id, order_id, client_id, description, resolution, strategy))
    memory.add_incident({"id": iid, "type": type, "truck_id": truck_id, "client_id": client_id,
                         "description": description, "resolution": resolution, "strategy": strategy})
    return iid
