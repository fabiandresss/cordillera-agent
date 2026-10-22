"""Memoria del agente.

- Corta (continuidad del flujo): checkpointer SQLite de LangGraph, un thread_id por jornada.
- Larga y semántica: ChromaDB con dos colecciones (incidentes y políticas) y embeddings.
"""
import logging
import re
import sqlite3

from . import config, db
from .llm import get_embeddings

log = logging.getLogger("cordillera.memory")


# ------------------------------------------------------------ memoria corta
def get_checkpointer():
    from langgraph.checkpoint.sqlite import SqliteSaver

    conn = sqlite3.connect(config.checkpoint_path(), check_same_thread=False)
    return SqliteSaver(conn)


# ------------------------------------------------------------ memoria larga
def _store(name: str):
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=f"{name}_{config.embeddings_provider()}",
        embedding_function=get_embeddings(),
        persist_directory=str(config.chroma_dir()),
        collection_metadata={"hnsw:space": "cosine"},
    )


def _chunks(text: str, size: int = 500) -> list[str]:
    paras, out, cur = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()], [], ""
    for p in paras:
        if len(cur) + len(p) > size and cur:
            out.append(cur)
            cur = ""
        cur += (" " if cur else "") + p
    if cur:
        out.append(cur)
    return out


def index_all(force: bool = False) -> dict:
    """Indexa incidentes (desde SQLite) y políticas (.md). Idempotente."""
    res = {}
    inc, pol = _store("incidentes"), _store("politicas")
    if force:
        for s in (inc, pol):
            ids = s.get()["ids"]
            if ids:
                s.delete(ids=ids)
    if inc._collection.count() == 0:
        rows = db.rows("SELECT * FROM incidents")
        if rows:
            inc.add_texts(
                texts=[f"{r['description']} Resolución: {r['resolution']}" for r in rows],
                metadatas=[_meta(r) for r in rows],
                ids=[f"inc-{r['id']}" for r in rows])
        res["incidentes"] = len(rows)
    if pol._collection.count() == 0:
        texts, metas, ids = [], [], []
        for f in sorted(config.policies_dir().glob("*.md")):
            for i, ch in enumerate(_chunks(f.read_text(encoding="utf-8"))):
                texts.append(ch)
                metas.append({"source": f.name})
                ids.append(f"{f.stem}-{i}")
        pol.add_texts(texts=texts, metadatas=metas, ids=ids)
        res["politicas"] = len(texts)
    return res


def _meta(r: dict) -> dict:
    return {"type": r["type"] or "", "truck_id": r["truck_id"] or 0,
            "client_id": r["client_id"] or 0, "strategy": r["strategy"] or "",
            "resolution": r["resolution"] or ""}


def add_incident(row: dict):
    try:
        _store("incidentes").add_texts(
            texts=[f"{row['description']} Resolución: {row['resolution']}"],
            metadatas=[_meta(row)], ids=[f"inc-{row['id']}"])
    except Exception as e:  # la memoria nunca debe tumbar el flujo operativo
        log.warning("No se pudo indexar el incidente: %s", e)


def _search(name: str, query: str, k: int, threshold: float, flt: dict | None = None):
    try:
        hits = _store(name).similarity_search_with_relevance_scores(query, k=k, filter=flt)
    except Exception as e:
        log.warning("Recuperación semántica no disponible (%s): %s", name, e)
        return []
    return [{"text": d.page_content, "score": round(float(s), 3), "metadata": d.metadata}
            for d, s in hits if s >= threshold]


def search_incidents(query: str, k: int = 3, threshold: float | None = None,
                     incident_type: str | None = None) -> list[dict]:
    thr = config.similarity_threshold() if threshold is None else threshold
    flt = {"type": incident_type} if incident_type else None
    return _search("incidentes", query, k, thr, flt)


def search_policies(query: str, k: int = 2, threshold: float = 0.35) -> list[dict]:
    return _search("politicas", query, k, threshold)
