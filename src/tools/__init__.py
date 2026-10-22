"""Registro de herramientas expuestas al LLM (agente de consultas).

Las funciones puras viven en query.py / write.py / reasoning.py y se usan
directamente desde los nodos del grafo; aquí se envuelven como herramientas
de LangChain para el agente conversacional (src/qa_agent.py)."""
from langchain_core.tools import tool

from . import query, reasoning, write

QUERY_TOOLS = [tool(f) for f in (
    query.get_fleet_status, query.get_pending_orders, query.get_order, query.get_traffic,
    query.get_client_profile, query.get_route, query.search_past_incidents, query.search_policies)]

WRITE_TOOLS = [tool(f) for f in (write.notify_client,)]

REASONING_TOOLS = [tool(reasoning.classify_event)]

ALL_TOOLS = QUERY_TOOLS + WRITE_TOOLS + REASONING_TOOLS
