# Orquestación de componentes

## 1. Vista de componentes

![Arquitectura](diagramas/arquitectura.png)

| Capa | Módulo | Responsabilidad |
|---|---|---|
| Interfaz | `frontend/` (React + Vite) | Panel web con el kit *fintech-ui-react* (tema `indigo`): control, rutas, pedidos, memoria, asistente, ajustes |
| API | `api/main.py` (FastAPI) | Expone el agente por HTTP (`/api/events`, `/api/overview`, `/api/memory/search`, `/api/chat`…) y sirve el panel compilado |
| Fachada | `src/agent.py` | `DispatchAgent`: invoca el grafo con un `thread_id` por jornada |
| Orquestación | `src/graph.py`, `src/state.py` | Grafo LangGraph con aristas condicionales y estado tipado |
| Decisión | `src/planner.py` | Prioridad, asignación, secuenciación, validación y reparación (determinista) |
| Herramientas | `src/tools/query.py`, `write.py`, `reasoning.py` | Consulta, escritura y razonamiento |
| Memoria | `src/memory.py` | Checkpointer SQLite (corta) + ChromaDB (larga, semántica) |
| LLM | `src/llm.py` | Selector `groq` / `ollama` / `rules` y embeddings |
| Datos | `src/db.py`, `data/seed.py` | SQLite, geografía ficticia, tráfico simulado |
| Consultas | `src/qa_agent.py` | Agente ReAct (el LLM elige herramientas de solo lectura) |

## 2. Flujo del grafo

![Flujo](diagramas/flujo_grafo.png)

Diagrama exportado automáticamente por LangGraph: [`grafo_langgraph.mmd`](grafo_langgraph.mmd).

```mermaid
flowchart TD
    A[ingest_event] --> B[classify_event<br/>LLM + reglas + validación de ids]
    B -->|otro| X1[escalate]
    B -->|falta dato| X2[clarify]
    B -->|ok| C[retrieve_context<br/>ChromaDB: incidentes + políticas]
    C --> D[apply_event<br/>acción según el tipo de evento]
    D -->|sin acción| X3[record_only]
    D -->|sin replan| H
    D -->|necesita plan| E[plan<br/>planificador determinista]
    E --> F{validate}
    F -->|sin violaciones| G[execute]
    F -->|viola y repair&lt;3| R[repair] --> F
    F -->|agotado| P[escalate_partial] --> G
    G --> H[draft_notifications<br/>LLM redacta, plantilla de respaldo]
    H --> I[notify_and_log<br/>avisos, incidente en SQLite y Chroma, historial]
```

## 3. Secuencia de un escenario (avería de camión)

```mermaid
sequenceDiagram
    actor U as Despachador
    participant UI as Panel React + API FastAPI
    participant G as Grafo LangGraph
    participant L as LLM / reglas
    participant M as ChromaDB
    participant P as Planificador
    participant DB as SQLite
    U->>UI: "A las 11:00 el camión 3 se averió"
    UI->>G: handle(evento) [thread_id de la jornada]
    G->>L: classify_event
    L-->>G: averia, camión 3 (validado contra la BD)
    G->>M: search_incidents("camión 3 se averió")
    M-->>G: incidente similar (sim 0.72) → reasignar_a_mayor_capacidad
    G->>DB: avanzar reloj a 11:00, camión 3 = averiado
    G->>P: plan_orders(pedidos abiertos, camiones operativos)
    P-->>G: Plan (+ validate_plan / repair)
    G->>DB: cancelar plan previo, assign_orders, hojas de ruta
    G->>L: redactar avisos (si falla → plantilla)
    G->>DB: notify_client, log_incident
    G->>M: indexar incidente nuevo (memoria larga)
    G-->>UI: estado final + log de razonamiento
```

## 4. Memoria

| Tipo | Mecanismo | Qué guarda | Dónde se usa |
|---|---|---|---|
| Corta | `SqliteSaver` + `thread_id` | historial de eventos de la jornada, nº de replanificaciones | contar inestabilidad (≥3 replanes → aviso al supervisor), retomar tras reinicio |
| Larga | ChromaDB (coseno) + `nomic-embed-text` | incidentes pasados con su estrategia y resolución; políticas | sugerir estrategia (p. ej. reprogramar mañana para un cliente con ausencias), citar la política aplicable |

## 5. Tolerancia a fallos (degradación controlada)

| Falla | Reacción |
|---|---|
| LLM sin clave o caído | clasificación por reglas + plantillas de aviso |
| LLM clasifica mal | reglas de alta precisión prevalecen; `nuevo_dia` solo con confirmación de reglas |
| LLM inventa un id | se descarta contra la BD y se pide el dato |
| LLM redacta un aviso sin los datos exactos | se descarta y se usa plantilla |
| Embeddings / ChromaDB no disponibles | la búsqueda devuelve vacío; el flujo operativo continúa |
| Plan imposible | 3 intentos de reparación y luego escalamiento con el mejor plan posible |
