# Registro de decisiones de diseño (ADR)

> **Para el equipo (IE9):** la rúbrica y las reglas de uso de IA de la evaluación exigen que la
> **justificación técnica sea del equipo**. Cada decisión trae abajo lo que está **medido o
> documentado** en el repo (datos, pruebas, observaciones reales). Escriban en cada recuadro
> «Nuestra justificación» su argumento con sus palabras, apoyándose en esa evidencia.

---

## D1. Orquestación con LangGraph (grafo de estado) en vez de un agente ReAct único
**Qué se implementó:** `src/graph.py` con 13 nodos, 4 aristas condicionales y estado tipado (`AgentState`).
**Evidencia en el repo:**
- Flujo con ramas distintas por situación: ver `docs/diagramas/flujo_grafo.png`.
- El estado persiste por `thread_id` con `SqliteSaver` (prueba `test_s5b_estado_persiste_tras_reiniciar`).
- Existe además un agente ReAct (`src/qa_agent.py`) para consultas de solo lectura.
**Alternativas consideradas:** AutoGen, Haystack, ReAct único con todas las herramientas.
**Nuestra justificación:** _(completar)_

## D2. Planificación determinista + LLM solo para interpretar y redactar
**Qué se implementó:** `src/planner.py` (fórmulas en `docs/planificacion.md`).
**Evidencia observada:**
- Con `qwen2.5:1.5b` el LLM clasificó «Cliente ausente en el pedido 8» como `nuevo_dia`; sin guardarraíl habría replanificado todo el día (ver `docs/evidencia_ollama/` y `tests/test_classifier.py`).
- El planificador cumple capacidad y ventanas en las pruebas `test_nunca_supera_capacidad`, `test_vip_antes_que_normal_con_ventana_similar`.
- Los avisos redactados por el LLM a veces omitían o alteraban horas; se validan y se reemplazan por plantilla.
**Nuestra justificación:** _(completar)_

## D3. Proveedor de LLM intercambiable (Groq / Ollama / reglas) y todo gratuito
**Qué se implementó:** `src/llm.py` con `LLM_PROVIDER`.
**Evidencia:**
- Equipo de desarrollo: Intel i5-8250U, 7.9 GB de RAM, sin GPU dedicada → modelos de 7B no viables en local.
- `qwen2.5:1.5b` corre en CPU (~10–25 s por evento con 3–4 llamadas al LLM) pero con errores de clasificación.
- Escenario 6 (`test_s6_llm_caido_usa_reglas`): sin clave de Groq el flujo se completa igualmente.
**Nuestra justificación:** _(completar)_

## D4. Memoria corta (checkpointer SQLite) y larga (ChromaDB + embeddings)
**Qué se implementó:** `src/memory.py`.
**Evidencia medida (nomic-embed-text, coseno):**

| Consulta | Mejor similitud |
|---|---|
| «el camión 3 se averió en zona norte» (tipo avería) | 0.717 |
| «se me rompió una rueda del camión» | 0.667 |
| «Cliente ausente en el pedido 8» (tipo entrega fallida) | 0.739 |
| «El cliente VIP necesita su pedido urgente…» | 0.773 |
| «pasta de dientes» (ruido) | 0.540 |

El umbral se fijó en **0.60**: deja pasar paráfrasis y descarta ruido (test `test_umbral_filtra_ruido`).
Con embeddings por hashing (solo pruebas) los puntajes son menores y se usa 0.25.
**Observación:** los incidentes que el agente registra hoy quedan recuperables en la misma jornada
(`test_incidente_nuevo_se_vuelve_recuperable`).
**Nuestra justificación:** _(completar)_

## D5. SQLite como almacén operativo
**Qué se implementó:** `src/db.py`; esquema de 6 tablas, sin servidor.
**Evidencia:** reproducible con `python data/seed.py` (semilla 42); tests aíslados con BD temporal.
**Nuestra justificación:** _(completar)_

## D6. Guardarraíles contra alucinaciones y fallos
**Qué se implementó:** validación de ids contra la BD, petición de datos faltantes, escalamiento de eventos no reconocidos, reparación acotada a 3 intentos.
**Evidencia:** `test_s7_eventos_ambiguos`, `test_s8_plan_imposible_escala`, `test_id_inexistente_se_descarta`.
**Nuestra justificación:** _(completar)_

## Limitaciones conocidas (para discutir en la presentación)
- Geografía y tráfico simulados (6 zonas, matriz de distancias fija); sin APIs reales de mapas.
- Capacidad por jornada (una sola carga por camión); no modela múltiples viajes al depósito.
- Heurística voraz con reparación local: no garantiza el óptimo (VRP real requeriría OR-Tools).
- Los avisos se simulan (`outputs/outbox.jsonl`); no se envían correos reales.
- Un LLM de 1.5B es débil en *tool calling*; por eso las decisiones críticas son código.
