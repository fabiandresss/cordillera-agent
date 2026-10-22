# Escenario 1 averia

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

## Evento 2: «A las 11:00 el camión 3 se averió en la Zona Norte»

```text
📥 Evento recibido: «A las 11:00 el camión 3 se averió en la Zona Norte»
🧠 Clasificado como averia (fuente: reglas) · camión 3
📚 Memoria larga: incidente similar (similitud 0.725): «El camión no arranca por batería descargada en zona Norte Resolución: Se reasignaron las entregas pendientes a…» → estrategia previa: reasignar_a_mayor_capacidad
📖 Política aplicable: 02_averia_de_camion.md
⏱️ Reloj simulado a 11:00; entregas ya realizadas: [9, 1, 3, 20, 5, 11, 10, 18, 12]
🔧 Camión 3 marcado como averiado; sus entregas pendientes se reasignan
🗺️ Plan calculado a las 11:00: 16 entregas en 4 camiones
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 16 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 9 {'cambio_camion': 6, 'cambio': 3}
🗃️ Incidente #16 registrado y almacenado en memoria larga
```

**Resultado:** `ok`

Ejemplos de avisos a clientes:
- (cliente 9, pedido 24, cambio_camion) Hola Laboratorio Andes: por un imprevisto operativo, su pedido #24 será atendido por otro camión. La hora estimada se mantiene hacia las 14:00. Transportes Cordillera.
- (cliente 7, pedido 15, cambio_camion) Hola Taller Mecánico Eje: por un imprevisto operativo, su pedido #15 será atendido por otro camión. La hora estimada se mantiene hacia las 14:13. Transportes Cordillera.
- (cliente 9, pedido 4, cambio_camion) Hola Laboratorio Andes: por un imprevisto operativo, su pedido #4 será atendido por otro camión. La hora estimada se mantiene hacia las 12:00. Transportes Cordillera.

## Resumen verificable

```json
{
  "camion3": "averiado",
  "asignaciones_camion3": 0,
  "asignaciones_total": 16,
  "entregados": 9
}
```
