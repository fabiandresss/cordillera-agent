from src import planner
from src.planner import Plan
from src.tools import query


def _setup():
    now = 8 * 60
    return (query.open_orders(), query.operational_trucks(now), query.client_tiers(), now)


def test_vip_antes_que_normal_con_ventana_similar(world):
    o_norm = dict(id=101, client_id=1, zone="Centro", weight_kg=50, priority=2, window_start=480, window_end=720)
    o_vip = dict(id=102, client_id=2, zone="Centro", weight_kg=50, priority=2, window_start=480, window_end=720)
    t = [dict(id=1, remaining_kg=1000, start_zone="Industrial", shift_end=1080, start_time=480)]
    plan, _ = planner.plan_orders([o_norm, o_vip], t, query.client_tiers(), 480)
    seq = [s.order_id for s in plan.by_truck()[1]]
    assert seq.index(102) < seq.index(101)


def test_nunca_supera_capacidad(world):
    orders, trucks, clients, now = _setup()
    plan, ctx = planner.plan_orders(orders, trucks, clients, now)
    for tid, stops in plan.by_truck().items():
        assert sum(ctx["orders"][s.order_id]["weight_kg"] for s in stops) <= ctx["trucks"][tid]["remaining_kg"]
    assert not any(v["type"] == "CAPACIDAD" for v in planner.validate_plan(plan, ctx))


def test_pedido_que_no_cabe_queda_sin_asignar(world):
    big = dict(id=999, client_id=1, zone="Sur", weight_kg=9999, priority=1, window_start=480, window_end=900)
    t = [dict(id=1, remaining_kg=800, start_zone="Industrial", shift_end=1080, start_time=480)]
    plan, _ = planner.plan_orders([big], t, {1: "normal"}, 480)
    assert plan.unassigned == [{"order_id": 999, "reason": "sin_capacidad"}]


def test_estabilidad_con_plan_previo(world):
    orders, trucks, clients, now = _setup()
    plan, _ = planner.plan_orders(orders, trucks, clients, now)
    prev = {s.order_id: s.truck_id for s in plan.stops}
    plan2, _ = planner.plan_orders(orders, trucks, clients, now, prev)
    same = sum(1 for s in plan2.stops if prev[s.order_id] == s.truck_id)
    assert same >= len(prev) * 0.8       # un replan idéntico casi no mueve pedidos


def test_validacion_detecta_ventana_y_reparacion_mejora(world):
    # Dos pedidos urgentes en zonas opuestas en un solo camión -> atraso; con dos camiones se arregla.
    a = dict(id=1, client_id=1, zone="Norte", weight_kg=50, priority=3, window_start=480, window_end=520)
    b = dict(id=2, client_id=1, zone="Sur", weight_kg=50, priority=3, window_start=480, window_end=520)
    trucks = [dict(id=1, remaining_kg=1000, start_zone="Industrial", shift_end=1080, start_time=480),
              dict(id=2, remaining_kg=1000, start_zone="Industrial", shift_end=1080, start_time=480)]
    ctx = {"orders": {1: a, 2: b}, "trucks": {t["id"]: t for t in trucks}, "clients": {1: "normal"}, "now": 480}
    bad = Plan(stops=planner.simulate_route(trucks[0], [a, b], 480))
    assert any(v["type"] == "VENTANA" for v in planner.validate_plan(bad, ctx))
    fixed, moves = planner.repair(bad, ctx)
    assert moves >= 1
    assert len(planner.validate_plan(fixed, ctx)) < len(planner.validate_plan(bad, ctx))


def test_sobrepasar_turno_se_detecta(world):
    o = dict(id=1, client_id=1, zone="Sur", weight_kg=10, priority=1, window_start=1000, window_end=1100)
    t = dict(id=1, remaining_kg=100, start_zone="Industrial", shift_end=1005, start_time=480)
    stops = planner.simulate_route(t, [o], 480)
    assert stops[0].over_shift


def test_plan_serializable(world):
    orders, trucks, clients, now = _setup()
    plan, _ = planner.plan_orders(orders, trucks, clients, now)
    assert Plan.from_dict(plan.to_dict()).to_dict() == plan.to_dict()
