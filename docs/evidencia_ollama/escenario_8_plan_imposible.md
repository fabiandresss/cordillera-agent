# Escenario 8 plan imposible

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
- (cliente 2, pedido 1, inicial) Hola, Farmacia Santa Rita. Su pedido #1 está programado para llegar a las 09:00 (ventana 09:00-11:30). Transporte Cordillera.
- (cliente 5, pedido 3, inicial) Hola Clínica Dental Sonrisa, su pedido #3 está programado para llegar a las 09:15 (ventana 09:00-11:30). Transportes Cordillera.

## Evento 2: «A las 11:00 el cliente 2 (VIP) necesita el pedido 14 antes de las 11:01»

```text
📥 Evento recibido: «A las 11:00 el cliente 2 (VIP) necesita el pedido 14 antes de las 11:01»
🧠 Clasificado como vip_urgente (fuente: LLM) · pedido 14, cliente 2
📚 Memoria larga: incidente similar (similitud 0.776): «Laboratorio VIP pidió adelantar su pedido por una muestra con cadena de frío Resolución: Se adelantó el pedido…» → estrategia previa: priorizar_y_reordenar
📖 Política aplicable: 01_prioridad_clientes_vip.md
⏱️ Reloj simulado a 11:00; entregas ya realizadas: [9, 1, 3, 20, 5, 11, 10, 18, 12]
⭐ Pedido 14 sube a prioridad 4, hora límite 11:01; se reordena la ruta
🗺️ Plan calculado a las 11:00: 16 entregas en 5 camiones
⚠️ Validación: 1 violaciones (VENTANA)
🔧 Reparación 1/3: 0 pedidos movidos (sin mejora posible)
⚠️ Validación: 1 violaciones (VENTANA)
🚨 Pedidos [14] no pueden cumplir su ventana → escalado; se ejecuta el mejor plan posible
📝 Plan ejecutado: 16 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 10 {'cambio_camion': 4, 'riesgo': 1, 'cambio': 5}
🗃️ Incidente #16 registrado y almacenado en memoria larga
```

**Resultado:** `escalated`

Ejemplos de avisos a clientes:
- (cliente 9, pedido 21, cambio_camion) Hola Laboratorio Andes: por un imprevisto operativo, su pedido #21 será atendido por otro camión. La hora estimada es aproximadamente las 14:00. Gracias por su comprensión.
- (cliente 2, pedido 14, riesgo) Hola, Farmacia Santa Rita. Su pedido #14 podría llegar a las 11:04. Un supervisor lo contactará. Gracias.
- (cliente 10, pedido 23, cambio) Hola Boutique Marina,

Querido cliente, por un malentendido, su pedido #23 se despide hacia las 12:10 (antes 14:19). Lo siento por la confusión. Gracias por su paciencia.

Transportes Cordillera.

## Resumen verificable

```json
{
  "resultado": "escalated",
  "violaciones": 1
}
```
