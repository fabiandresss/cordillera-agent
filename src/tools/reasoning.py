"""Herramienta de RAZONAMIENTO: clasifica un evento en lenguaje natural.

Estrategia en dos capas:
1. Extractor determinista (regex) de entidades: camión, pedido, cliente, hora, hora límite.
2. LLM con salida estructurada para el *tipo* de evento y un resumen. Su salida se valida
   contra la BD (un id inventado se descarta). Si el LLM falla o no hay LLM, se usa
   un clasificador por palabras clave: el flujo nunca se cae.
"""
import logging
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .. import db
from ..llm import get_llm

log = logging.getLogger("cordillera.reasoning")

EventType = Literal["nuevo_dia", "averia", "vip_urgente", "entrega_fallida", "otro"]


class EventClassification(BaseModel):
    tipo: EventType = Field(description="Tipo de evento operativo")
    resumen: str = Field(description="Resumen breve del evento, máximo 20 palabras")


KEYWORDS: list[tuple[str, str]] = [
    ("averia", r"aver[ií]|falla|pana\b|no arranca|se detuvo|choc|pinch|descompu|accident|sobrecalent"),
    ("entrega_fallida", r"ausente|no se pudo|nadie|rechaz|no recib|direcci[oó]n incorrecta|fallid|cerrado|no (?:lo )?encontr"),
    ("vip_urgente", r"\bvip\b|urgent|urgencia|lo antes posible|adelantar|prioridad|cuanto antes"),
    ("nuevo_dia", r"inicio de (?:la )?jornada|nuevo d[ií]a|planificar el d[ií]a|comenzar la jornada|arranque del d[ií]a"),
]

_NUM = r"\s*(?:n[°ºo.]*\s*)?#?(\d+)"


def extract_entities(text: str) -> dict:
    t = text.lower()
    g = lambda pat: (int(m.group(1)) if (m := re.search(pat, t)) else None)  # noqa: E731
    hour = None
    if m := re.search(r"(?:a las|las|desde las)\s*(\d{1,2})(?::(\d{2}))?", t):
        hour = int(m.group(1)) * 60 + int(m.group(2) or 0)
    elif m := re.search(r"\b(\d{1,2}):(\d{2})\b", t):
        hour = int(m.group(1)) * 60 + int(m.group(2))
    deadline = None
    if m := re.search(r"antes de las\s*(\d{1,2})(?::(\d{2}))?", t):
        deadline = int(m.group(1)) * 60 + int(m.group(2) or 0)
        if hour is not None and re.search(r"antes de las", t) and hour == deadline:
            hour = None  # "antes de las 12" es hora límite, no hora del evento
    return {
        "truck_id": g(r"cami[oó]n" + _NUM),
        "order_id": g(r"pedido" + _NUM),
        "client_id": g(r"cliente" + _NUM),
        "event_minute": hour,
        "deadline": deadline,
    }


def classify_by_keywords(text: str) -> str:
    t = text.lower()
    for tipo, pat in KEYWORDS:
        if re.search(pat, t):
            return tipo
    return "otro"


def classify_with_llm(text: str) -> tuple[Optional[EventClassification], str]:
    """Devuelve (clasificación, motivo_si_falla)."""
    try:
        llm = get_llm()
    except Exception as e:  # sin clave, proveedor inválido…
        return None, f"LLM no disponible: {e}"
    if llm is None:
        return None, "modo rules (sin LLM)"
    prompt = (
        "Eres el despachador de una empresa de transporte. Clasifica el evento en UNA categoría:\n"
        "- nuevo_dia: inicio de jornada / planificar el día\n"
        "- averia: un camión tiene una avería, falla o accidente\n"
        "- vip_urgente: un cliente VIP pide urgencia o adelantar un pedido\n"
        "- entrega_fallida: no se pudo entregar (ausente, rechazo, dirección incorrecta)\n"
        "- otro: cualquier otra cosa\n\n"
        f"Evento: {text}"
    )
    try:
        return llm.with_structured_output(EventClassification).invoke(prompt), ""
    except Exception as e:
        return None, f"fallo del LLM: {type(e).__name__}"


def classify_event(text: str) -> dict:
    """Clasifica un evento y extrae entidades validadas. Devuelve un dict serializable."""
    ents = extract_entities(text)
    kw = classify_by_keywords(text)
    llm_out, why = classify_with_llm(text)

    if llm_out is not None:
        resumen = llm_out.resumen
        if llm_out.tipo == kw:
            tipo, source = kw, "llm"
        elif kw != "otro":
            # Las reglas son de alta precisión: prevalecen sobre un LLM pequeño que se equivoca.
            tipo, source = kw, f"reglas (prevalecieron sobre el LLM, que dijo '{llm_out.tipo}')"
        elif llm_out.tipo == "nuevo_dia":
            # 'nuevo_dia' reinicia el plan completo: solo se acepta si las reglas lo confirman.
            tipo, source = "otro", "reglas (se rechazó 'nuevo_dia' propuesto solo por el LLM)"
        else:
            tipo, source = llm_out.tipo, "llm"
    else:
        tipo, source, resumen = kw, f"reglas ({why})", text.strip()[:120]

    # Guardarraíl anti-alucinación: los ids deben existir en la BD
    if ents["truck_id"] and not db.one("SELECT 1 FROM trucks WHERE id=?", (ents["truck_id"],)):
        ents["invalid_truck"] = ents.pop("truck_id")
        ents["truck_id"] = None
    if ents["order_id"] and not db.one("SELECT 1 FROM orders WHERE id=?", (ents["order_id"],)):
        ents["invalid_order"] = ents.pop("order_id")
        ents["order_id"] = None
    if ents["client_id"] and not db.one("SELECT 1 FROM clients WHERE id=?", (ents["client_id"],)):
        ents["invalid_client"] = ents.pop("client_id")
        ents["client_id"] = None

    # Entidad faltante -> pedir más datos en vez de adivinar
    missing = None
    if tipo == "averia" and not ents["truck_id"]:
        missing = "¿Qué camión tiene la avería? Indica el número de camión."
    elif tipo == "entrega_fallida" and not ents["order_id"]:
        missing = "¿Qué pedido no se pudo entregar? Indica el número de pedido."
    elif tipo == "vip_urgente" and not ents["order_id"]:
        if ents["client_id"]:
            o = db.one("SELECT id FROM orders WHERE client_id=? AND status IN ('pendiente','asignado') "
                       "ORDER BY window_end LIMIT 1", (ents["client_id"],))
            if o:
                ents["order_id"] = o["id"]
        if not ents["order_id"]:
            missing = "¿Qué pedido necesita urgencia? Indica el número de pedido."

    return {"tipo": tipo, "resumen": resumen, "source": source, "missing_info": missing, **ents}
