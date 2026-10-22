"""Agente conversacional (ReAct con tool-calling) para consultar el estado de la operación.

Aquí SÍ es el LLM quien decide qué herramienta de consulta usar y con qué
argumentos. Es de solo lectura: las decisiones que modifican el plan pasan
siempre por el grafo determinista (src/graph.py).
Memoria corta de la conversación: checkpointer + thread_id.
"""
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from .llm import get_llm
from .tools import QUERY_TOOLS

SYSTEM_PROMPT = (
    "Eres el asistente de operaciones de Transportes Cordillera. Responde en español, breve y "
    "preciso, usando SIEMPRE las herramientas para obtener datos; nunca inventes ids, horas ni "
    "estados. Las horas están en minutos desde medianoche salvo los campos *_hm. Si un dato no "
    "existe, dilo. No puedes modificar el plan: para cambios, indica que se registre un evento."
)


def build_qa_agent(model=None, checkpointer=None):
    model = model or get_llm()
    if model is None:
        raise RuntimeError("El agente conversacional requiere un LLM (LLM_PROVIDER=groq|ollama).")
    return create_agent(model=model, tools=QUERY_TOOLS, system_prompt=SYSTEM_PROMPT,
                        checkpointer=checkpointer or MemorySaver())


def ask(agent, question: str, thread_id: str = "chat-1") -> tuple[str, list[str]]:
    """Devuelve (respuesta, herramientas_usadas)."""
    res = agent.invoke({"messages": [{"role": "user", "content": question}]},
                       {"configurable": {"thread_id": thread_id}})
    used = [tc["name"] for m in res["messages"] if isinstance(m, AIMessage) for tc in (m.tool_calls or [])]
    return res["messages"][-1].content, used
