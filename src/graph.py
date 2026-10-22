"""Grafo LangGraph del agente de despacho.

ingest → classify ─┬─ otro ───────────────► escalate ► END
                   ├─ falta dato ─────────► clarify ► END
                   └─ ok ► retrieve_context ► apply_event ─┬─ sin acción ─► END
                                                           ├─ sin replan ─► draft_notifications
                                                           └─ plan ► validate ─┬─ ok ──────► execute
                                                                               ├─ viola ───► repair ► validate
                                                                               └─ agotado ─► escalate_partial ► execute
                                        execute ► draft_notifications ► notify_and_log ► END
"""
import logging
import re

from langgraph.graph import END, StateGraph

from . import config, db, memory, planner
from .llm import get_llm
from .planner import Plan
from .state import AgentState
from .tools import query, reasoning, write

log = logging.getLogger("cordillera.graph")


def _say(state: AgentState, msg: str) -> list:
    return list(state.get("log", [])) + [msg]


def _hist(state: AgentState, outcome: str) -> dict:
    c = state.get("classification") or {}
    return {"evento": c.get("tipo", "desconocido"), "hora": db.hm(db.get_now()),
            "pedido": c.get("order_id"), "camion": c.get("truck_id"), "resultado": outcome}


def _ctx() -> dict:
    now = db.get_now()
    orders = query.open_orders()
    trucks = query.operational_trucks(now)
    return {"orders": {o["id"]: o for o in orders}, "trucks": {t["id"]: t for t in trucks},
            "clients": query.client_tiers(), "now": now}


# ---------------------------------------------------------------- nodos
def ingest_event(state: AgentState) -> dict:
    text = " ".join(state["event_text"].split())
    return {"event_text": text, "log": _say(state, f"📥 Evento recibido: «{text}»")}


def classify_event(state: AgentState) -> dict:
    c = reasoning.classify_event(state["event_text"])
    msg = f"🧠 Clasificado como **{c['tipo']}** (fuente: {c['source']})"
    ids = {k: c[k] for k in ("truck_id", "order_id", "client_id") if c.get(k)}
    if ids:
        msg += f" · entidades: {ids}"
    for k in ("invalid_truck", "invalid_order", "invalid_client"):
        if c.get(k):
            msg += f" · ⚠️ id inexistente descartado ({k}={c[k]})"
    return {"classification": c, "log": _say(state, msg)}


def route_after_classify(state: AgentState) -> str:
    c = state["classification"]
    if c["tipo"] == "otro":
        return "escalate"
    if c.get("missing_info"):
        return "clarify"
    return "retrieve_context"


def clarify(state: AgentState) -> dict:
    q = state["classification"]["missing_info"]
    return {"needs_info": q, "outcome": "needs_info", "history": [_hist(state, "needs_info")],
            "log": _say(state, f"❓ Faltan datos: {q}")}


def escalate(state: AgentState) -> dict:
    write.notify_supervisor(
        f"Evento no clasificable: «{state['event_text']}»",
        "Revisar manualmente; el agente no tomó ninguna acción sobre el plan.")
    return {"escalated": True, "outcome": "escalated", "history": [_hist(state, "escalated")],
            "log": _say(state, "🚨 Evento no reconocido → escalado al supervisor (sin cambios al plan)")}


def retrieve_context(state: AgentState) -> dict:
    """Memoria larga: incidentes pasados parecidos y política aplicable."""
    c = state["classification"]
    lines = list(state.get("log", []))
    context, policies, hint = [], [], None
    if c["tipo"] != "nuevo_dia":
        query_text = re.sub(r"^\s*a las \d{1,2}(:\d{2})?[,:]?\s*", "", state["event_text"], flags=re.I)
        context = memory.search_incidents(query_text, k=5,
                                          incident_type=c["tipo"])
        policies = memory.search_policies(f"{c['tipo']} {query_text}", k=1)
        if context:
            top = context[0]
            hint = {"strategy": top["metadata"].get("strategy"), "score": top["score"],
                    "client_id": top["metadata"].get("client_id") or None, "text": top["text"]}
            lines.append(f"📚 Memoria larga: incidente similar (similitud {top['score']}): "
                         f"«{top['text'][:110]}…» → estrategia previa: {hint['strategy']}")
        else:
            lines.append("📚 Memoria larga: sin incidentes suficientemente parecidos")
        if policies:
            lines.append(f"📖 Política aplicable: {policies[0]['metadata'].get('source')}")
    return {"context": context, "policies": policies, "hint": hint, "log": lines}


def apply_event(state: AgentState) -> dict:
    """Actúa sobre el mundo según el evento: la decisión adaptativa ocurre aquí."""
    c, hint = state["classification"], state.get("hint")
    lines = list(state.get("log", []))
    tipo = c["tipo"]
    if c.get("event_minute") is not None and tipo != "nuevo_dia":
        done = write.advance_clock(c["event_minute"])
        lines.append(f"⏱️ Reloj simulado a {db.hm(db.get_now())}; entregas ya realizadas: {done or 'ninguna'}")
    now = db.get_now()
    out: dict = {"decision": None, "needs_plan": False}

    if tipo == "nuevo_dia":
        lines.append(f"🗓️ Inicio de jornada {config.JORNADA}: se planifican todos los pedidos abiertos")
        out.update(needs_plan=True, decision={"kind": "nuevo_dia"})

    elif tipo == "averia":
        tid = c["truck_id"]
        t = db.one("SELECT status FROM trucks WHERE id=?", (tid,))
        if t["status"] == "averiado":
            lines.append(f"ℹ️ El camión {tid} ya estaba averiado: no hay cambios")
            out.update(outcome="sin_accion")
        else:
            write.set_truck_status(tid, "averiado")
            lines.append(f"🔧 Camión {tid} marcado como averiado; sus entregas pendientes se reasignan")
            out.update(needs_plan=True, decision={"kind": "averia", "truck_id": tid,
                                                  "strategy": "reasignar_a_mayor_capacidad"})

    elif tipo == "vip_urgente":
        oid = c["order_id"]
        o = db.one("SELECT * FROM orders WHERE id=?", (oid,))
        if o["status"] not in ("pendiente", "asignado"):
            lines.append(f"ℹ️ El pedido {oid} está '{o['status']}': no se puede priorizar")
            out.update(outcome="sin_accion")
        else:
            write.set_order_priority(oid, 4, c.get("deadline"))
            lim = f", hora límite {db.hm(c['deadline'])}" if c.get("deadline") else ""
            lines.append(f"⭐ Pedido {oid} sube a prioridad 4{lim}; se reordena la ruta")
            out.update(needs_plan=True, decision={"kind": "vip", "order_id": oid,
                                                  "client_id": o["client_id"],
                                                  "strategy": "priorizar_y_reordenar"})

    elif tipo == "entrega_fallida":
        oid = c["order_id"]
        o = db.one("SELECT * FROM orders WHERE id=?", (oid,))
        attempts = write.register_failed_delivery(oid)
        lines.append(f"📦 Entrega fallida del pedido {oid} (intento {attempts}/{config.MAX_FAILED_ATTEMPTS})")
        if attempts >= config.MAX_FAILED_ATTEMPTS:
            write.escalate_order(oid)
            write.notify_supervisor(f"Pedido {oid} acumula {attempts} intentos fallidos",
                                    "Decidir devolución o contacto directo con el cliente (política 03).")
            lines.append("🚨 Política de 2 intentos: pedido escalado al supervisor, no se reprograma solo")
            out.update(escalated=True, decision={"kind": "fallida_escalada", "order_id": oid,
                                                 "client_id": o["client_id"],
                                                 "strategy": "escalar_supervisor"})
        else:
            prior = query.get_client_profile(o["client_id"])["failed_deliveries"]
            mem_next_day = any(h["metadata"].get("strategy") == "reprogramar_manana"
                               and h["metadata"].get("client_id") == o["client_id"]
                               for h in state.get("context", []))
            has_room = now + 180 <= config.SHIFT_END - 30
            if mem_next_day or prior >= 2 or not has_room:
                why = ("la memoria recuerda ausencias previas de este cliente" if mem_next_day
                       else "el cliente acumula ausencias previas" if prior >= 2
                       else "no hay holgura en la jornada")
                write.reschedule_order(oid, 9 * 60, 12 * 60, same_day=False)
                lines.append(f"📅 Se reprograma para mañana 09:00-12:00 ({why})")
                out.update(decision={"kind": "fallida_manana", "order_id": oid,
                                     "client_id": o["client_id"], "strategy": "reprogramar_manana"})
            else:
                write.reschedule_order(oid, now + 60, now + 180, same_day=True)
                lines.append(f"🔁 Reintento el mismo día en ventana {db.hm(now + 60)}-{db.hm(now + 180)}")
                out.update(needs_plan=True, decision={"kind": "fallida_hoy", "order_id": oid,
                                                      "client_id": o["client_id"],
                                                      "strategy": "reintento_misma_jornada"})
    return {**out, "log": lines}


def record_only(state: AgentState) -> dict:
    """Evento sin cambios al plan: solo queda registrado en la memoria corta."""
    return {"history": [_hist(state, "sin_accion")]}


def route_after_apply(state: AgentState) -> str:
    if state.get("outcome") == "sin_accion":
        return "record_only"
    return "plan" if state.get("needs_plan") else "draft_notifications"


def plan_node(state: AgentState) -> dict:
    ctx = _ctx()
    prev = query.previous_plan()
    if not ctx["trucks"]:
        write.notify_supervisor("No quedan camiones operativos", "Contratar transporte externo.")
        return {"escalated": True, "outcome": "escalated", "plan": Plan().to_dict(),
                "log": _say(state, "🚨 No quedan camiones operativos → escalado")}
    plan, _ = planner.plan_orders(list(ctx["orders"].values()), list(ctx["trucks"].values()),
                                  ctx["clients"], ctx["now"], {k: v["truck_id"] for k, v in prev.items()})
    n_trucks = len(plan.by_truck())
    msg = f"🗺️ Plan calculado a las {db.hm(ctx['now'])}: {len(plan.stops)} entregas en {n_trucks} camiones"
    if plan.unassigned:
        msg += f", {len(plan.unassigned)} sin asignar"
    return {"plan": plan.to_dict(), "prev_plan": {str(k): v for k, v in prev.items()},
            "repair_count": 0, "log": _say(state, msg)}


def validate_node(state: AgentState) -> dict:
    ctx = _ctx()
    v = planner.validate_plan(Plan.from_dict(state["plan"]), ctx)
    if v:
        kinds = sorted({x["type"] for x in v})
        msg = f"⚠️ Validación: {len(v)} violaciones ({', '.join(kinds)})"
    else:
        msg = "✅ Validación: el plan cumple capacidad, ventanas y turnos"
    return {"violations": v, "log": _say(state, msg)}


def route_after_validate(state: AgentState) -> str:
    if not state["violations"]:
        return "execute"
    if state.get("repair_count", 0) < config.MAX_REPLANS:
        return "repair"
    return "escalate_partial"


def repair_node(state: AgentState) -> dict:
    ctx = _ctx()
    new_plan, moves = planner.repair(Plan.from_dict(state["plan"]), ctx)
    count = state.get("repair_count", 0) + 1
    msg = f"🔧 Reparación {count}/{config.MAX_REPLANS}: {moves} pedidos movidos"
    if moves == 0:
        count = config.MAX_REPLANS  # no hay mejora posible: no insistir
        msg += " (sin mejora posible)"
    return {"plan": new_plan.to_dict(), "repair_count": count, "log": _say(state, msg)}


def escalate_partial(state: AgentState) -> dict:
    late = sorted({v.get("order_id") for v in state["violations"] if v.get("order_id")})
    write.notify_supervisor(
        f"Plan con pedidos fuera de ventana tras {config.MAX_REPLANS} reparaciones: {late}",
        "Contactar a esos clientes para renegociar la hora o autorizar un camión extra.")
    return {"escalated": True,
            "log": _say(state, f"🚨 Pedidos {late} no pueden cumplir su ventana → escalado; "
                               "se ejecuta el mejor plan posible")}


def execute_node(state: AgentState) -> dict:
    plan = Plan.from_dict(state["plan"])
    write.cancel_planned_assignments()
    errors = []
    for tid, stops in plan.by_truck().items():
        r = write.assign_orders(tid, [s.order_id for s in stops], [s.eta for s in stops])
        if not r["ok"]:
            errors.append(r["error"])
    sheets = [write.write_route_sheet(t["id"]) for t in db.rows("SELECT id FROM trucks ORDER BY id")]
    msg = f"📝 Plan ejecutado: {len(plan.stops)} asignaciones y {len(sheets)} hojas de ruta generadas"
    if errors:
        msg += f" · errores: {errors}"
    if plan.unassigned:
        write.notify_supervisor(f"Pedidos sin camión disponible: {plan.unassigned}", "Evaluar transporte externo.")
        msg += f" · sin asignar: {[u['order_id'] for u in plan.unassigned]}"
    return {"log": _say(state, msg)}


# ---------------------------------------------------------------- notificaciones
def _template(kind: str, f: dict) -> str:
    n, oid = f["name"], f["order_id"]
    ws, we = f.get("ws", ""), f.get("we", "")
    if kind == "inicial":
        return (f"Hola {n}: su pedido #{oid} está programado para llegar hacia las {f['eta']} "
                f"(ventana {ws}-{we}). Transportes Cordillera.")
    if kind == "cambio":
        return (f"Hola {n}: por un imprevisto operativo, su pedido #{oid} ahora llegará hacia las {f['eta']} "
                f"(antes {f['old_eta']}). Disculpe las molestias. Transportes Cordillera.")
    if kind == "cambio_camion":
        return (f"Hola {n}: por un imprevisto operativo, su pedido #{oid} será atendido por otro camión. "
                f"La hora estimada se mantiene hacia las {f['eta']}. Transportes Cordillera.")
    if kind == "vip":
        return (f"Hola {n}: confirmamos la entrega prioritaria de su pedido #{oid}, estimada hacia las "
                f"{f['eta']}. Transportes Cordillera.")
    if kind == "riesgo":
        return (f"Hola {n}: su pedido #{oid} podría llegar fuera de la ventana {ws}-{we} (estimado {f['eta']}). "
                f"Un supervisor lo contactará. Transportes Cordillera.")
    if kind == "fallida_hoy":
        return (f"Hola {n}: no pudimos entregar su pedido #{oid}. Reintentaremos hoy hacia las {f['eta']}. "
                f"Transportes Cordillera.")
    if kind == "fallida_manana":
        return (f"Hola {n}: no pudimos entregar su pedido #{oid}. Lo reprogramamos para mañana entre "
                f"09:00 y 12:00. Transportes Cordillera.")
    return (f"Hola {n}: tras dos intentos sin éxito con su pedido #{oid}, un supervisor se contactará "
            f"con usted. Transportes Cordillera.")


_BAD_WORDS = ("redact", "aviso", "base:", "plantilla", "formato", "como modelo")


def _valid_llm_message(out: str, f: dict) -> bool:
    low = out.lower()
    if not (30 <= len(out) <= 320) or any(w in low for w in _BAD_WORDS):
        return False
    # debe conservar los datos exactos: nº de pedido y hora estimada (si corresponde)
    return str(f["order_id"]) in out and (not f.get("eta") or f["eta"] in out)


def _write_message(kind: str, f: dict, llm, budget: list) -> str:
    """El LLM redacta con tono natural; si su salida no conserva los datos, se usa la plantilla."""
    base = _template(kind, f)
    if llm is None or budget[0] <= 0:
        return base
    budget[0] -= 1
    try:
        out = llm.invoke(
            "Reescribe este aviso para un cliente con tono amable, en español, máximo 2 frases, sin "
            f"saludos extra ni comentarios. Conserva el número de pedido y las horas EXACTAS.\n\n{base}"
        ).content.strip()
        if _valid_llm_message(out, f):
            return out
        log.info("Mensaje del LLM descartado por no conservar los datos; se usa plantilla")
    except Exception as e:
        log.info("LLM no disponible para redactar (%s); se usa plantilla", type(e).__name__)
    return base


def draft_notifications(state: AgentState) -> dict:
    d, prev = state.get("decision") or {}, state.get("prev_plan") or {}
    try:
        llm = get_llm()
    except Exception:
        llm = None
    budget = [3]  # máx. mensajes redactados por LLM (rapidez en CPU); el resto, plantilla
    notes, kinds = [], {}

    def fact(oid, eta=None, old=None):
        o = db.one("SELECT o.*, c.name FROM orders o JOIN clients c ON c.id=o.client_id WHERE o.id=?", (oid,))
        return o, {"name": o["name"], "order_id": oid, "ws": db.hm(o["window_start"]),
                   "we": db.hm(o["window_end"]), "eta": db.hm(eta) if eta is not None else "",
                   "old_eta": db.hm(old) if old is not None else ""}

    if state.get("plan"):
        plan = Plan.from_dict(state["plan"])
        for s in plan.stops:
            o, f = fact(s.order_id, s.eta, (prev.get(str(s.order_id)) or {}).get("eta"))
            before = prev.get(str(s.order_id))
            if d.get("kind") == "nuevo_dia":
                kind = "inicial" if not s.late else "riesgo"
            elif s.late:
                kind = "riesgo"
            elif d.get("kind") == "vip" and s.order_id == d["order_id"]:
                kind = "vip"
            elif d.get("kind") == "fallida_hoy" and s.order_id == d["order_id"]:
                kind = "fallida_hoy"
            elif before is None:
                kind = "inicial"
            elif abs(before["eta"] - s.eta) >= 15:
                kind = "cambio"
            elif before["truck_id"] != s.truck_id:
                kind = "cambio_camion"
            else:
                continue
            notes.append((o["client_id"], s.order_id, kind, f))
    if d.get("kind") in ("fallida_manana", "fallida_escalada"):
        o, f = fact(d["order_id"])
        notes.append((o["client_id"], d["order_id"], d["kind"], f))

    out = []
    for cid, oid, kind, f in notes:
        out.append({"client_id": cid, "order_id": oid, "kind": kind,
                    "message": _write_message(kind, f, llm, budget)})
        kinds[kind] = kinds.get(kind, 0) + 1
    return {"notifications": out,
            "log": _say(state, f"✉️ Avisos redactados: {len(out)} {kinds or ''}".strip())}


def notify_and_log(state: AgentState) -> dict:
    c, d = state["classification"], state.get("decision") or {}
    for n in state.get("notifications", []):
        write.notify_client(n["client_id"], n["message"], n["order_id"])
    lines = list(state.get("log", []))
    replans = state.get("replans_today", 0)
    outcome = "escalated" if state.get("escalated") else "ok"

    if c["tipo"] != "nuevo_dia":
        plan = Plan.from_dict(state["plan"]) if state.get("plan") else Plan()
        prev = state.get("prev_plan") or {}
        moved = sum(1 for s in plan.stops
                    if prev.get(str(s.order_id)) and prev[str(s.order_id)]["truck_id"] != s.truck_id)
        desc = f"{c['resumen']}" if c["source"] == "llm" else state["event_text"]
        res = (f"Estrategia {d.get('strategy', 'n/d')}: {moved} pedidos cambiaron de camión, "
               f"{len(state.get('notifications', []))} clientes avisados"
               + ("; caso escalado al supervisor" if state.get("escalated") else ""))
        iid = write.log_incident(
            c["tipo"], desc, res, d.get("strategy", ""), c.get("truck_id") or d.get("truck_id"),
            c.get("order_id"), d.get("client_id"))
        lines.append(f"🗃️ Incidente #{iid} registrado y almacenado en memoria larga")
        if state.get("plan"):
            replans += 1
        if replans >= 3 and not state.get("escalated"):
            write.notify_supervisor(f"{replans} replanificaciones en la jornada",
                                    "Posible inestabilidad operativa (política 06): revisar la flota.")
            lines.append(f"🚨 Memoria corta: {replans} replanificaciones hoy → aviso de inestabilidad al supervisor")
            outcome = "escalated"
    return {"outcome": outcome, "history": [_hist(state, outcome)], "replans_today": replans, "log": lines}


# ---------------------------------------------------------------- construcción
def build_graph(checkpointer=None):
    g = StateGraph(AgentState)
    for name, fn in [("ingest_event", ingest_event), ("classify_event", classify_event),
                     ("clarify", clarify), ("escalate", escalate), ("record_only", record_only),
                     ("retrieve_context", retrieve_context), ("apply_event", apply_event),
                     ("plan", plan_node), ("validate", validate_node), ("repair", repair_node),
                     ("escalate_partial", escalate_partial), ("execute", execute_node),
                     ("draft_notifications", draft_notifications), ("notify_and_log", notify_and_log)]:
        g.add_node(name, fn)
    g.set_entry_point("ingest_event")
    g.add_edge("ingest_event", "classify_event")
    g.add_conditional_edges("classify_event", route_after_classify,
                            {"escalate": "escalate", "clarify": "clarify",
                             "retrieve_context": "retrieve_context"})
    g.add_edge("clarify", END)
    g.add_edge("escalate", END)
    g.add_edge("retrieve_context", "apply_event")
    g.add_conditional_edges("apply_event", route_after_apply,
                            {"record_only": "record_only", "plan": "plan",
                             "draft_notifications": "draft_notifications"})
    g.add_edge("record_only", END)
    g.add_edge("plan", "validate")
    g.add_conditional_edges("validate", route_after_validate,
                            {"execute": "execute", "repair": "repair",
                             "escalate_partial": "escalate_partial"})
    g.add_edge("repair", "validate")
    g.add_edge("escalate_partial", "execute")
    g.add_edge("execute", "draft_notifications")
    g.add_edge("draft_notifications", "notify_and_log")
    g.add_edge("notify_and_log", END)
    return g.compile(checkpointer=checkpointer)
