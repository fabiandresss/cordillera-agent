# Escenario 7 eventos ambiguos

_Proveedor LLM: `ollama` · embeddings: `ollama` · umbral de similitud: 0.6_

## Evento 1: «Inicio de jornada»

```text
📥 Evento recibido: «Inicio de jornada»
🧠 Clasificado como nuevo_dia (fuente: LLM)
🗓️ Inicio de jornada 2026-10-26: se planifican todos los pedidos abiertos
🗺️ Plan calculado a las 08:00: 25 entregas en 5 camiones
⚠️ Validación: 1 violaciones (VENTANA)
🔧 Reparación 1/3: 1 pedidos movidos
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 25 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 25 {'inicial': 25}
```

**Resultado:** `ok`

Ejemplos de avisos a clientes:
- (cliente 9, pedido 9, inicial) Hola Laboratorio Andes, su pedido #9 está programado para llegar a las 08:19 (ventana 08:00-11:00). Transportes Cordillera.
- (cliente 2, pedido 1, inicial) Hola Farmacia Santa Rita, su pedido #1 está programado para llegar a las 09:00 (ventana 09:00-11:30). Transporte Cordillera.
- (cliente 5, pedido 3, inicial) Hola Clínica Dental Sonrisa, su pedido #3 está programado para llegar a las 09:15 (ventana 09:00-11:30). Transportes Cordillera.

## Evento 2: «No funciona nada!»

```text
📥 Evento recibido: «No funciona nada!»
🧠 Clasificado como otro (fuente: LLM)
🚨 Evento no reconocido → escalado al supervisor (sin cambios al plan)
```

**Resultado:** `escalated`

## Evento 3: «Se averió un camión»

```text
📥 Evento recibido: «Se averió un camión»
🧠 Clasificado como averia (fuente: LLM)
❓ Faltan datos: ¿Qué camión tiene la avería? Indica el número de camión.
```

**Resultado:** `needs_info`
 · pregunta al usuario: ¿Qué camión tiene la avería? Indica el número de camión.

## Evento 4: «El camión 99 se averió»

```text
📥 Evento recibido: «El camión 99 se averió»
🧠 Clasificado como averia (fuente: LLM) · ⚠️ camión 99 no existe: se descartó
❓ Faltan datos: ¿Qué camión tiene la avería? Indica el número de camión.
```

**Resultado:** `needs_info`
 · pregunta al usuario: ¿Qué camión tiene la avería? Indica el número de camión.

## Resumen verificable

```json
{
  "resultados": [
    "escalated",
    "needs_info",
    "needs_info"
  ]
}
```
