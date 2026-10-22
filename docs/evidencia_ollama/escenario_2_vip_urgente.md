# Escenario 2 vip urgente

_Proveedor LLM: `ollama` · embeddings: `ollama` · umbral de similitud: 0.6_

## Evento 1: «Inicio de jornada»

```text
📥 Evento recibido: «Inicio de jornada»
🧠 Clasificado como nuevo_dia (fuente: llm)
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
- (cliente 9, pedido 9, inicial) Hola Laboratorio Andes,

Su pedido #9 está programado para llegar a las 08:19 (ventana 08:00-11:00). Transportes Cordillera.

Gracias por preferirnos.
- (cliente 2, pedido 1, inicial) Hola, Farmacia Santa Rita. Su pedido #1 está programado para llegar a las 09:00 (ventana 09:00-11:30). Transporte Cordillera.
- (cliente 5, pedido 3, inicial) Hola Clínica Dental Sonrisa, su pedido #3 está programado para llegar a las 09:15 (ventana 09:00-11:30). Transportes Cordillera.

## Evento 2: «A las 10:00 el cliente 2 (VIP) necesita su pedido 14 antes de las 12:00»

```text
📥 Evento recibido: «A las 10:00 el cliente 2 (VIP) necesita su pedido 14 antes de las 12:00»
🧠 Clasificado como vip_urgente (fuente: llm) · entidades: {'order_id': 14, 'client_id': 2}
📚 Memoria larga: incidente similar (similitud 0.759): «Laboratorio VIP pidió adelantar su pedido por una muestra con cadena de frío Resolución: Se adelantó el pedido…» → estrategia previa: priorizar_y_reordenar
📖 Política aplicable: 01_prioridad_clientes_vip.md
⏱️ Reloj simulado a 10:00; entregas ya realizadas: [9, 1, 3, 20, 10, 18]
⭐ Pedido 14 sube a prioridad 4, hora límite 12:00; se reordena la ruta
🗺️ Plan calculado a las 10:00: 19 entregas en 5 camiones
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 19 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 11 {'vip': 1, 'cambio': 8, 'cambio_camion': 2}
🗃️ Incidente #16 registrado y almacenado en memoria larga
```

**Resultado:** `ok`

Ejemplos de avisos a clientes:
- (cliente 2, pedido 14, vip) Hola Farmacia Santa Rita,

Confirmamos la entrega prioritaria de su pedido #14. Estimada hacia las 12:00. Transporte Cordillera.

Gracias por su confianza en nosotros.
- (cliente 2, pedido 17, cambio) Hola Farmacia Santa Rita,

Queremos informarle que su pedido #17 llegará a las 12:19 (antes 11:19). Gracias por su comprensión.

Transportes Cordillera.
- (cliente 9, pedido 5, cambio) Hola Laboratorio Andes,

Por un imprevisto operativo, su pedido #5 llegará a las 12:42 (antes 11:00). Gracias por su comprensión.

Transportes Cordillera.

## Resumen verificable

```json
{
  "prioridad": 4,
  "eta_hm": "12:00",
  "eta": 720,
  "seq": 1,
  "truck": 1
}
```
