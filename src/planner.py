"""Planificador determinista de despacho.

La priorización, la asignación a camiones, la secuenciación y la validación
viven aquí (código verificable). El LLM nunca decide prioridades.

Fórmulas documentadas en docs/planificacion.md.
"""
from dataclasses import asdict, dataclass, field

from . import config, db


# ------------------------------------------------------------------ modelos
@dataclass
class Stop:
    order_id: int
    truck_id: int
    seq: int
    zone: str
    eta: int            # minuto del día en que se entrega
    window_start: int
    window_end: int
    late: bool = False  # llega después del cierre de la ventana
    over_shift: bool = False


@dataclass
class Plan:
    stops: list[Stop] = field(default_factory=list)
    unassigned: list[dict] = field(default_factory=list)  # {order_id, reason}

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Plan":
        return Plan([Stop(**s) for s in d["stops"]], list(d["unassigned"]))

    def by_truck(self) -> dict[int, list[Stop]]:
        out: dict[int, list[Stop]] = {}
        for s in sorted(self.stops, key=lambda s: (s.truck_id, s.seq)):
            out.setdefault(s.truck_id, []).append(s)
        return out


# ------------------------------------------------------------------ prioridad
def urgency_score(order: dict, tier: str, now: int, depot: str = db.DEPOT_ZONE) -> float:
    """score = prioridad*100 + 50 si VIP + 100 / max(holgura, 5)."""
    slack = order["window_end"] - now - db.travel_minutes(depot, order["zone"], now)
    return order["priority"] * 100 + (50 if tier == "VIP" else 0) + 100 / max(slack, 5)


def _sequence_key(order: dict, tier: str, cur_zone: str, cur_t: int) -> float:
    """Clave de secuenciación (menor = antes): cierre de ventana + 2*viaje,
    bonificada en minutos por prioridad y por cliente VIP."""
    travel = db.travel_minutes(cur_zone, order["zone"], cur_t)
    return (order["window_end"] + 2 * travel
            - 60 * (order["priority"] - 1) - (30 if tier == "VIP" else 0))


# ------------------------------------------------------------------ simulación
def simulate_route(truck: dict, ordered: list[dict], now: int) -> list[Stop]:
    """Calcula ETAs de una secuencia fija de pedidos para un camión."""
    zone = truck["start_zone"]
    t = max(now, truck.get("start_time", now))
    stops = []
    for i, o in enumerate(ordered, 1):
        arrive = t + db.travel_minutes(zone, o["zone"], t)
        eta = max(arrive, o["window_start"])
        done = eta + config.SERVICE_MIN
        stops.append(Stop(
            order_id=o["id"], truck_id=truck["id"], seq=i, zone=o["zone"], eta=eta,
            window_start=o["window_start"], window_end=o["window_end"],
            late=eta > o["window_end"], over_shift=done > truck["shift_end"]))
        zone, t = o["zone"], done
    return stops


def _lateness(stops: list[Stop]) -> int:
    return sum(max(0, s.eta - s.window_end) + (5000 if s.over_shift else 0) for s in stops)


# ------------------------------------------------------------------ planificación
def plan_orders(orders: list[dict], trucks: list[dict], clients: dict[int, str],
                now: int, prev: dict[int, int] | None = None) -> tuple[Plan, dict]:
    """Planifica todos los pedidos dados con los camiones disponibles.

    orders : pedidos por entregar (id, client_id, zone, weight_kg, priority, window_*)
    trucks : camiones operativos (id, remaining_kg, start_zone, shift_end, start_time)
    clients: client_id -> tier
    prev   : order_id -> truck_id del plan anterior (estabilidad: evita mover pedidos sin necesidad)
    Devuelve (Plan, contexto_para_reparar).
    """
    prev = prev or {}
    tier = lambda o: clients.get(o["client_id"], "normal")  # noqa: E731
    ranked = sorted(orders, key=lambda o: -urgency_score(o, tier(o), now))

    load = {t["id"]: 0 for t in trucks}
    last_zone = {t["id"]: t["start_zone"] for t in trucks}
    sets: dict[int, list[dict]] = {t["id"]: [] for t in trucks}
    unassigned = []

    # Fase A: asignación por prioridad, cercanía y balance de carga
    for o in ranked:
        cands = [t for t in trucks if t["remaining_kg"] - load[t["id"]] >= o["weight_kg"]]
        if not cands:
            unassigned.append({"order_id": o["id"], "reason": "sin_capacidad"})
            continue

        def cost(t):
            km = db.DISTANCES[(last_zone[t["id"]], o["zone"])]
            sticky = -3.0 if prev.get(o["id"]) == t["id"] else 0.0
            return km + sticky + 0.002 * load[t["id"]]

        best = min(cands, key=cost)
        sets[best["id"]].append(o)
        load[best["id"]] += o["weight_kg"]
        last_zone[best["id"]] = o["zone"]

    # Fase B: secuenciación por camión
    plan = Plan(unassigned=unassigned)
    for t in trucks:
        pending, ordered = list(sets[t["id"]]), []
        zone, clock = t["start_zone"], max(now, t.get("start_time", now))
        while pending:
            nxt = min(pending, key=lambda o: _sequence_key(o, tier(o), zone, clock))
            pending.remove(nxt)
            ordered.append(nxt)
            clock += db.travel_minutes(zone, nxt["zone"], clock) + config.SERVICE_MIN
            zone = nxt["zone"]
        plan.stops += simulate_route(t, ordered, now)

    ctx = {"orders": {o["id"]: o for o in orders}, "trucks": {t["id"]: t for t in trucks},
           "clients": clients, "now": now}
    return plan, ctx


# ------------------------------------------------------------------ validación
def validate_plan(plan: Plan, ctx: dict) -> list[dict]:
    """Devuelve violaciones tipadas: CAPACIDAD, VENTANA, TURNO."""
    out = []
    for tid, stops in plan.by_truck().items():
        cap = ctx["trucks"][tid]["remaining_kg"]
        total = sum(ctx["orders"][s.order_id]["weight_kg"] for s in stops)
        if total > cap:
            out.append({"type": "CAPACIDAD", "truck_id": tid, "detail": f"{total}kg > {cap}kg"})
        for s in stops:
            if s.late:
                out.append({"type": "VENTANA", "truck_id": tid, "order_id": s.order_id,
                            "detail": f"ETA {db.hm(s.eta)} > cierre {db.hm(s.window_end)}"})
            if s.over_shift:
                out.append({"type": "TURNO", "truck_id": tid, "order_id": s.order_id,
                            "detail": f"termina después de {db.hm(ctx['trucks'][tid]['shift_end'])}"})
    return out


# ------------------------------------------------------------------ reparación
def repair(plan: Plan, ctx: dict) -> tuple[Plan, int]:
    """Intenta corregir atrasos moviendo pedidos entre camiones/posiciones.
    Acepta un movimiento solo si reduce el atraso total. Devuelve (plan, nº movimientos)."""
    orders, trucks, now = ctx["orders"], ctx["trucks"], ctx["now"]
    routes = {tid: [orders[s.order_id] for s in stops] for tid, stops in plan.by_truck().items()}
    for tid in trucks:
        routes.setdefault(tid, [])

    def sim(tid, seq):
        return simulate_route(trucks[tid], seq, now)

    def total_lateness():
        return sum(_lateness(sim(tid, seq)) for tid, seq in routes.items())

    moves = 0
    late_ids = [s.order_id for s in plan.stops if s.late or s.over_shift]
    for oid in late_ids:
        src = next(tid for tid, seq in routes.items() if any(o["id"] == oid for o in seq))
        base = total_lateness()
        best = (base, None)
        order = orders[oid]
        for tid in trucks:
            used = sum(o["weight_kg"] for o in routes[tid] if o["id"] != oid)
            if used + order["weight_kg"] > trucks[tid]["remaining_kg"]:
                continue
            remaining_src = [o for o in routes[src] if o["id"] != oid]
            target = remaining_src if tid == src else routes[tid]
            for pos in range(len(target) + 1):
                cand = target[:pos] + [order] + target[pos:]
                if tid == src:
                    new = _lateness(sim(tid, cand)) + sum(
                        _lateness(sim(t2, s2)) for t2, s2 in routes.items() if t2 != tid)
                else:
                    new = (_lateness(sim(src, remaining_src)) + _lateness(sim(tid, cand))
                           + sum(_lateness(sim(t2, s2)) for t2, s2 in routes.items()
                                 if t2 not in (src, tid)))
                if new < best[0]:
                    best = (new, (tid, pos))
        if best[1]:
            tid, pos = best[1]
            routes[src] = [o for o in routes[src] if o["id"] != oid]
            routes[tid].insert(pos, order)
            moves += 1

    new_plan = Plan(unassigned=list(plan.unassigned))
    for tid, seq in routes.items():
        new_plan.stops += sim(tid, seq)
    return new_plan, moves
