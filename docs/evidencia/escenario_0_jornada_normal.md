# Escenario 0 jornada normal

_Proveedor LLM: `rules` · embeddings: `ollama` · umbral de similitud: 0.6_

## Evento 1: «Inicio de jornada»

```text
📥 Evento recibido: «Inicio de jornada»
🧠 Clasificado como nuevo_dia (fuente: reglas)
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
- (cliente 9, pedido 9, inicial) Hola Laboratorio Andes: su pedido #9 está programado para llegar hacia las 08:19 (ventana 08:00-11:00). Transportes Cordillera.
- (cliente 2, pedido 1, inicial) Hola Farmacia Santa Rita: su pedido #1 está programado para llegar hacia las 09:00 (ventana 09:00-11:30). Transportes Cordillera.
- (cliente 5, pedido 3, inicial) Hola Clínica Dental Sonrisa: su pedido #3 está programado para llegar hacia las 09:15 (ventana 09:00-11:30). Transportes Cordillera.

## Resumen verificable

```json
{
  "asignaciones": 25,
  "camiones": 5
}
```
