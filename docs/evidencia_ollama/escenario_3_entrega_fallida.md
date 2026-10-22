# Escenario 3 entrega fallida

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
- (cliente 9, pedido 9, inicial) Hola Laboratorio Andes, su pedido #9 está programado para llegar a las 08:19 (ventana 08:00-11:00). Transportes Cordillera.
- (cliente 2, pedido 1, inicial) Hola Farmacia Santa Rita, su pedido #1 está programado para llegar a las 09:00 (ventana 09:00-11:30). Transporte Cordillera.
- (cliente 5, pedido 3, inicial) Hola Clínica Dental Sonrisa, su pedido #3 está programado para llegar a las 09:15 (ventana 09:00-11:30). Transportes Cordillera.

## Evento 2: «A las 10:00 cliente ausente en el pedido 11»

```text
📥 Evento recibido: «A las 10:00 cliente ausente en el pedido 11»
🧠 Clasificado como entrega_fallida (fuente: reglas (prevalecieron sobre el LLM, que dijo 'nuevo_dia')) · entidades: {'order_id': 11}
📚 Memoria larga: incidente similar (similitud 0.743): «Nadie recibió el pedido en la oficina, portería sin autorización Resolución: Se reintentó el mismo día con avi…» → estrategia previa: reintento_misma_jornada
📖 Política aplicable: 03_entregas_fallidas.md
⏱️ Reloj simulado a 10:00; entregas ya realizadas: [9, 1, 3, 20, 10, 18]
📦 Entrega fallida del pedido 11 (intento 1/2)
🔁 Reintento el mismo día en ventana 11:00-13:00
🗺️ Plan calculado a las 10:00: 19 entregas en 5 camiones
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 19 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 13 {'fallida_hoy': 1, 'cambio_camion': 3, 'cambio': 9}
🗃️ Incidente #16 registrado y almacenado en memoria larga
```

**Resultado:** `ok`

Ejemplos de avisos a clientes:
- (cliente 4, pedido 11, fallida_hoy) Hola Librería Pluma, no pudimos entregar su pedido #11. Reintentaremos hoy a las 11:19. Gracias por su paciencia.
- (cliente 9, pedido 21, cambio_camion) Hola Laboratorio Andes: por un imprevisto operativo, su pedido #21 será atendido por otro camión. La hora estimada es aproximadamente las 14:00. Gracias por su comprensión.
- (cliente 2, pedido 17, cambio) Hola, Farmacia Santa Rita. Mi pedido #17 llegará a las 10:09 (antes 11:19). Gracias por su comprensión. Estamos agradecidos por su paciencia. Gracias.

## Evento 3: «A las 13:00 nuevamente ausente en el pedido 11, nadie lo recibió»

```text
📥 Evento recibido: «A las 13:00 nuevamente ausente en el pedido 11, nadie lo recibió»
🧠 Clasificado como entrega_fallida (fuente: reglas (prevalecieron sobre el LLM, que dijo 'nuevo_dia')) · entidades: {'order_id': 11}
📚 Memoria larga: incidente similar (similitud 0.761): «A las 10:00 cliente ausente en el pedido 11 Resolución: Estrategia reintento_misma_jornada: 3 pedidos cambiaro…» → estrategia previa: reintento_misma_jornada
📖 Política aplicable: 03_entregas_fallidas.md
⏱️ Reloj simulado a 13:00; entregas ya realizadas: [5, 11, 17, 6, 16, 14, 7, 4, 19, 12]
📦 Entrega fallida del pedido 11 (intento 2/2)
🚨 Política de 2 intentos: pedido escalado al supervisor, no se reprograma solo
✉️ Avisos redactados: 1 {'fallida_escalada': 1}
🗃️ Incidente #17 registrado y almacenado en memoria larga
```

**Resultado:** `escalated`

Ejemplos de avisos a clientes:
- (cliente 4, pedido 11, fallida_escalada) Hola, querido cliente. Nos comunicaremos con usted para resolver el problema con su pedido #11. Gracias por su comprensión.

## Resumen verificable

```json
{
  "intentos": 2,
  "estado_final": "fallido"
}
```
