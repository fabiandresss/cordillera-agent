"""Punto de entrada del agente: ejecuta eventos sobre el grafo con memoria."""
import copy
import uuid

from . import memory
from .graph import build_graph

_FRESH = {
    "classification": None, "context": [], "policies": [], "hint": None, "plan": None,
    "prev_plan": {}, "violations": [], "repair_count": 0, "escalated": False,
    "needs_info": None, "notifications": [], "decision": None, "needs_plan": False,
    "outcome": "", "log": [],
}


class DispatchAgent:
    """Agente de despacho con memoria corta (checkpointer) y larga (Chroma)."""

    def __init__(self, thread_id: str | None = None, persist: bool = True, index: bool = True):
        self.thread_id = thread_id or f"jornada-{uuid.uuid4().hex[:10]}"
        self.graph = build_graph(memory.get_checkpointer() if persist else None)
        if index:
            memory.index_all()

    @property
    def _cfg(self):
        return {"configurable": {"thread_id": self.thread_id}}

    def handle(self, event_text: str) -> dict:
        """Procesa un evento y devuelve el estado final (con el log de razonamiento)."""
        return self.graph.invoke({**copy.deepcopy(_FRESH), "event_text": event_text}, self._cfg)

    def state(self) -> dict:
        """Estado persistido de la jornada (memoria corta)."""
        snap = self.graph.get_state(self._cfg)
        return dict(snap.values) if snap else {}
