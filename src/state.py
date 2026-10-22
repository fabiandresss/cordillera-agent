import operator
from typing import Annotated, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # --- entrada del evento actual (se reinicia en cada invocación)
    event_text: str
    classification: Optional[dict]
    context: list          # incidentes pasados recuperados (memoria larga)
    policies: list         # fragmentos de política recuperados
    hint: Optional[dict]   # estrategia sugerida por la memoria
    plan: Optional[dict]
    prev_plan: dict        # order_id -> {truck_id, eta} antes del replan
    violations: list
    repair_count: int
    escalated: bool
    needs_info: Optional[str]
    notifications: list
    decision: Optional[dict]   # decisión tomada por apply_event (tipo y parámetros)
    needs_plan: bool
    outcome: str
    log: list              # trazabilidad del razonamiento del agente
    # --- memoria corta: persiste entre eventos de la misma jornada (thread_id)
    history: Annotated[list, operator.add]
    replans_today: int
