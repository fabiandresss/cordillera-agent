"""Escenarios de demo reutilizables (pytest + generación de evidencia).

Cada escenario recibe un DispatchAgent y devuelve (lista de (evento, estado_final), resumen_dict).
"""
from src import db

START = "Inicio de jornada"


def _play(agent, events):
    return [(e, agent.handle(e)) for e in events]


def _planned(truck_id=None):
    sql = "SELECT * FROM assignments WHERE status='planificado'"
    if truck_id:
        return db.rows(sql + " AND truck_id=?", (truck_id,))
    return db.rows(sql)


def s0_jornada_normal(agent):
    res = _play(agent, [START])
    return res, {"asignaciones": len(_planned()), "camiones": len({a["truck_id"] for a in _planned()})}


def s1_averia(agent):
    res = _play(agent, [START, "A las 11:00 el camión 3 se averió en la Zona Norte"])
    return res, {"camion3": db.one("SELECT status FROM trucks WHERE id=3")["status"],
                 "asignaciones_camion3": len(_planned(3)), "asignaciones_total": len(_planned()),
                 "entregados": db.one("SELECT COUNT(*) n FROM orders WHERE status='entregado'")["n"]}


def s2_vip_urgente(agent):
    res = _play(agent, [START, "A las 10:00 el cliente 2 (VIP) necesita su pedido 14 antes de las 12:00"])
    a = db.one("SELECT * FROM assignments WHERE order_id=14 AND status='planificado'")
    o = db.one("SELECT * FROM orders WHERE id=14")
    return res, {"prioridad": o["priority"], "eta_hm": db.hm(a["eta"]), "eta": a["eta"],
                 "seq": a["seq"], "truck": a["truck_id"]}


def s3_entrega_fallida(agent):
    """Primer fallo (cliente sin historial) -> reintento hoy; segundo fallo -> escalamiento."""
    res = _play(agent, [START, "A las 10:00 cliente ausente en el pedido 11",
                        "A las 13:00 nuevamente ausente en el pedido 11, nadie lo recibió"])
    o = db.one("SELECT * FROM orders WHERE id=11")
    return res, {"intentos": o["attempts"], "estado_final": o["status"]}


def s4_memoria_larga(agent):
    res = _play(agent, [START, "A las 11:00 el camión 2 no arranca, la batería está descargada"])
    st = res[-1][1]
    return res, {"recuerdos": len(st["context"]),
                 "estrategia_recordada": (st["hint"] or {}).get("strategy"),
                 "similitud": (st["hint"] or {}).get("score")}


def s5_cadena_y_memoria_corta(agent):
    """Avería + VIP + entrega fallida en la misma jornada: la memoria corta cuenta replanificaciones."""
    res = _play(agent, [START, "A las 09:30 el camión 3 se averió",
                        "A las 10:30 el cliente 2 (VIP) pide urgente el pedido 14 antes de las 12:00",
                        "A las 12:30 cliente ausente en el pedido 11"])
    st = agent.state()
    return res, {"eventos_en_memoria": len(st["history"]), "replans_hoy": st["replans_today"],
                 "camion3": db.one("SELECT status FROM trucks WHERE id=3")["status"]}


def s6_llm_caido(agent):
    res = _play(agent, [START, "A las 11:00 el camión 4 se averió"])
    return res, {"fuente": res[-1][1]["classification"]["source"]}


def s7_eventos_ambiguos(agent):
    res = _play(agent, [START, "No funciona nada!", "Se averió un camión", "El camión 99 se averió"])
    return res, {"resultados": [s["outcome"] for _, s in res[1:]]}


def s8_plan_imposible(agent):
    res = _play(agent, [START, "A las 11:00 el cliente 2 (VIP) necesita el pedido 14 antes de las 11:01"])
    return res, {"resultado": res[-1][1]["outcome"], "violaciones": len(res[-1][1]["violations"])}


ALL = [
    ("escenario_0_jornada_normal", s0_jornada_normal),
    ("escenario_1_averia", s1_averia),
    ("escenario_2_vip_urgente", s2_vip_urgente),
    ("escenario_3_entrega_fallida", s3_entrega_fallida),
    ("escenario_4_memoria_larga", s4_memoria_larga),
    ("escenario_5_cadena_y_memoria_corta", s5_cadena_y_memoria_corta),
    ("escenario_6_llm_caido", s6_llm_caido),
    ("escenario_7_eventos_ambiguos", s7_eventos_ambiguos),
    ("escenario_8_plan_imposible", s8_plan_imposible),
]
