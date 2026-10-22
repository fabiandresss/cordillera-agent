# Escenario 4 memoria larga

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

## Evento 2: «A las 11:00 el camión 2 no arranca, la batería está descargada»

```text
📥 Evento recibido: «A las 11:00 el camión 2 no arranca, la batería está descargada»
🧠 Clasificado como averia (fuente: reglas) · camión 2
📚 Memoria larga: incidente similar (similitud 0.786): «El camión no arranca por batería descargada en zona Norte Resolución: Se reasignaron las entregas pendientes a…» → estrategia previa: reasignar_a_mayor_capacidad
📖 Política aplicable: 02_averia_de_camion.md
⏱️ Reloj simulado a 11:00; entregas ya realizadas: [9, 1, 3, 20, 5, 11, 10, 18, 12]
🔧 Camión 2 marcado como averiado; sus entregas pendientes se reasignan
🗺️ Plan calculado a las 11:00: 16 entregas en 4 camiones
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 16 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 13 {'cambio_camion': 8, 'cambio': 5}
🗃️ Incidente #16 registrado y almacenado en memoria larga
```

**Resultado:** `ok`

Ejemplos de avisos a clientes:
- (cliente 2, pedido 17, cambio_camion) Hola Farmacia Santa Rita: por un imprevisto operativo, su pedido #17 será atendido por otro camión. La hora estimada se mantiene hacia las 11:12. Transportes Cordillera.
- (cliente 9, pedido 21, cambio_camion) Hola Laboratorio Andes: por un imprevisto operativo, su pedido #21 será atendido por otro camión. La hora estimada se mantiene hacia las 14:00. Transportes Cordillera.
- (cliente 10, pedido 23, cambio_camion) Hola Boutique Marina: por un imprevisto operativo, su pedido #23 será atendido por otro camión. La hora estimada se mantiene hacia las 14:19. Transportes Cordillera.

## Resumen verificable

```json
{
  "recuerdos": 3,
  "estrategia_recordada": "reasignar_a_mayor_capacidad",
  "similitud": 0.786
}
```
