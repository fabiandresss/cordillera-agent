"""API HTTP del agente de despacho (FastAPI).

    python -m uvicorn api.main:app --port 8000

Sirve también el frontend compilado (frontend/dist) en «/», de modo que con un solo proceso
quedan la API y el panel. En desarrollo, el panel corre con Vite y hace proxy a /api.
"""
import json
import logging
import mimetypes
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src import config, db, memory, world
from src.agent import DispatchAgent
from src.llm import get_embeddings
from src.tools import query

# En Windows el registro puede declarar .js como text/plain y el navegador rechaza los módulos.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

log = logging.getLogger("cordillera.api")
DIST = config.ROOT / "frontend" / "dist"
PROVIDERS = ("rules", "ollama", "groq")


class EventIn(BaseModel):
    text: str = Field(min_length=2, max_length=500)


class ProviderIn(BaseModel):
    provider: str


class ChatIn(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class Ctx:
    """Estado del proceso: un agente por jornada (demo de un solo despachador)."""

    def __init__(self):
        self.lock = threading.RLock()
        self._agent: DispatchAgent | None = None
        self.qa = None
        self.qa_provider = None
        self.degraded: list[str] = []
        self.chat_thread = f"chat-{uuid.uuid4().hex[:10]}"
        self.last_result: dict | None = None

    def agent(self) -> DispatchAgent:
        with self.lock:
            if self._agent is None:
                self._prepare_world(fresh=True)
                self._agent = DispatchAgent(thread_id=f"jornada-{uuid.uuid4().hex[:10]}")
            return self._agent

    def _prepare_world(self, fresh: bool):
        """Verifica embeddings (degrada si Ollama no responde) y deja una jornada limpia."""
        if config.embeddings_provider() == "ollama" and "embeddings" not in self.degraded:
            try:
                get_embeddings().embed_query("ping")
            except Exception as e:  # Ollama apagado: se degrada a embeddings por hashing
                log.warning("Embeddings de Ollama no disponibles (%s): se usa modo 'fake'", type(e).__name__)
                os.environ["EMBEDDINGS_PROVIDER"] = "fake"
                os.environ.setdefault("SIMILARITY_THRESHOLD", "0.25")
                self.degraded.append("embeddings")
        keep = os.getenv("CORDILLERA_KEEP_STATE") == "1" and config.db_path().exists()
        if fresh and not keep:
            world.reseed()

    def reset(self):
        with self.lock:
            self._prepare_world(fresh=True)
            self._agent = DispatchAgent(thread_id=f"jornada-{uuid.uuid4().hex[:10]}")
            self.chat_thread = f"chat-{uuid.uuid4().hex[:10]}"
            self.qa = None
            self.last_result = None


def _jsonl(name: str, limit: int) -> list[dict]:
    p = config.output_dir() / name
    if not p.exists():
        return []
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[-limit:][::-1]


def _count_lines(name: str) -> int:
    p = config.output_dir() / name
    return sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip()) if p.exists() else 0


def build_overview(ctx: Ctx) -> dict:
    agent = ctx.agent()
    now = db.get_now()
    fleet = query.get_fleet_status()
    for t in fleet:
        t["utilization"] = round(100 * t["load_kg"] / t["capacity_kg"]) if t["capacity_kg"] else 0

    orders = db.rows(
        "SELECT o.id, o.zone, o.weight_kg, o.priority, o.window_start, o.window_end, o.status, o.attempts, "
        "c.id AS client_id, c.name AS client_name, c.tier, a.truck_id, a.eta, a.seq "
        "FROM orders o JOIN clients c ON c.id=o.client_id "
        "LEFT JOIN assignments a ON a.order_id=o.id AND a.status='planificado' ORDER BY o.id")
    for o in orders:
        o["window"] = f"{db.hm(o['window_start'])}–{db.hm(o['window_end'])}"
        o["eta_hm"] = db.hm(o["eta"]) if o["eta"] is not None else None
        o["at_risk"] = bool(o["eta"] is not None and o["eta"] > o["window_end"])

    routes = []
    for t in fleet:
        stops = db.rows(
            "SELECT a.seq, a.order_id, a.eta, a.status, o.zone, o.weight_kg, o.priority, o.window_start, "
            "o.window_end, c.name AS client_name, c.tier FROM assignments a "
            "JOIN orders o ON o.id=a.order_id JOIN clients c ON c.id=o.client_id "
            "WHERE a.truck_id=? AND a.status IN ('planificado','entregado') ORDER BY a.eta", (t["id"],))
        for s in stops:
            s["eta_hm"] = db.hm(s["eta"])
            s["window"] = f"{db.hm(s['window_start'])}–{db.hm(s['window_end'])}"
        routes.append({"truck_id": t["id"], "stops": stops})

    counts = {"pendiente": 0, "entregado": 0, "reprogramado": 0, "fallido": 0}
    for o in orders:
        key = "pendiente" if o["status"] in ("pendiente", "asignado") else o["status"]
        counts[key] = counts.get(key, 0) + 1

    st = agent.state()
    ok = [t for t in fleet if t["status"] != "averiado"]
    cap = sum(t["capacity_kg"] for t in ok) or 1
    return {
        "clock": {"minutes": now, "hm": db.hm(now), "jornada": config.JORNADA},
        "provider": config.llm_provider(),
        "embeddings": config.embeddings_provider(),
        "degraded": ctx.degraded,
        "thread_id": agent.thread_id,
        "kpis": {
            "pending": counts["pendiente"], "delivered": counts["entregado"],
            "rescheduled": counts["reprogramado"], "failed": counts["fallido"],
            "trucks_total": len(fleet), "trucks_ok": len(ok),
            "utilization": round(100 * sum(t["load_kg"] for t in ok) / cap),
            "replans": st.get("replans_today", 0),
            "notifications": _count_lines("outbox.jsonl"),
            "escalations": _count_lines("escalamientos.jsonl"),
            "at_risk": sum(1 for o in orders if o["at_risk"]),
        },
        "fleet": fleet, "orders": orders, "routes": routes, "order_counts": counts,
        "history": st.get("history", []),
        "incidents": db.rows("SELECT id, ts, type, truck_id, order_id, client_id, strategy, description, resolution "
                             "FROM incidents ORDER BY id DESC LIMIT 40"),
        "last_result": ctx.last_result,
        "outbox": _jsonl("outbox.jsonl", 12),
        "escalations": _jsonl("escalamientos.jsonl", 8),
    }


def create_app() -> FastAPI:
    ctx = Ctx()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        ctx.agent()  # calienta: crea datos, indexa memoria y abre el checkpointer
        yield

    app = FastAPI(title="Transportes Cordillera · Agente de despacho", version="1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/health")
    def health():
        return {"ok": True, "provider": config.llm_provider(), "embeddings": config.embeddings_provider(),
                "degraded": ctx.degraded}

    @app.get("/api/overview")
    def overview():
        with ctx.lock:
            return build_overview(ctx)

    @app.post("/api/events")
    def post_event(body: EventIn):
        text = body.text.strip()
        if len(text) < 2:
            raise HTTPException(422, "El evento está vacío")
        with ctx.lock:
            t0 = time.time()
            st = ctx.agent().handle(text)
            secs = round(time.time() - t0, 1)
            result = {
                "event": text, "log": st.get("log", []), "outcome": st.get("outcome", ""),
                "classification": st.get("classification"), "context": st.get("context", []),
                "policies": st.get("policies", []), "notifications": st.get("notifications", []),
                "needs_info": st.get("needs_info"), "escalated": bool(st.get("escalated")),
                "decision": st.get("decision"), "violations": st.get("violations", []), "seconds": secs,
            }
            ctx.last_result = result
            return {"result": result, "overview": build_overview(ctx)}

    @app.post("/api/reset")
    def reset():
        ctx.reset()
        with ctx.lock:
            return build_overview(ctx)

    @app.post("/api/provider")
    def set_provider(body: ProviderIn):
        p = body.provider.lower()
        if p not in PROVIDERS:
            raise HTTPException(422, f"Proveedor inválido. Usa uno de {PROVIDERS}")
        os.environ["LLM_PROVIDER"] = p
        ctx.qa = None
        warn = None
        if p == "groq" and not os.getenv("GROQ_API_KEY", "").strip():
            warn = "Falta GROQ_API_KEY en .env: el agente usará el modo de reglas."
        with ctx.lock:
            return {"warning": warn, "overview": build_overview(ctx)}

    @app.get("/api/memory/search")
    def memory_search(q: str = Query(min_length=2, max_length=200), k: int = Query(4, ge=1, le=10)):
        ctx.agent()
        return memory.search_incidents(q, k=k, threshold=0.0)

    @app.post("/api/chat")
    def chat(body: ChatIn):
        if config.llm_provider() == "rules":
            raise HTTPException(409, "El asistente requiere un LLM: cambia el proveedor a ollama o groq.")
        from src.qa_agent import ask, build_qa_agent

        with ctx.lock:
            ctx.agent()
            try:
                if ctx.qa is None or ctx.qa_provider != config.llm_provider():
                    ctx.qa, ctx.qa_provider = build_qa_agent(), config.llm_provider()
                answer, used = ask(ctx.qa, body.question.strip(), ctx.chat_thread)
            except Exception as e:
                log.warning("Fallo del asistente: %s", e)
                raise HTTPException(503, f"El asistente no pudo responder ({type(e).__name__}). Revisa el LLM.")
        return {"answer": answer, "tools": used}

    if DIST.exists():
        app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
    return app


app = create_app()
