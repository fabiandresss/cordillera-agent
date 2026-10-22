# Escenario 5 cadena y memoria corta

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

## Evento 2: «A las 09:30 el camión 3 se averió»

```text
📥 Evento recibido: «A las 09:30 el camión 3 se averió»
🧠 Clasificado como averia (fuente: LLM) · camión 3
📚 Memoria larga: incidente similar (similitud 0.622): «El camión no arranca por batería descargada en zona Norte Resolución: Se reasignaron las entregas pendientes a…» → estrategia previa: reasignar_a_mayor_capacidad
📖 Política aplicable: 02_averia_de_camion.md
⏱️ Reloj simulado a 09:30; entregas ya realizadas: [9, 1, 3, 10]
🔧 Camión 3 marcado como averiado; sus entregas pendientes se reasignan
🗺️ Plan calculado a las 09:30: 21 entregas en 4 camiones
⚠️ Validación: 1 violaciones (VENTANA)
🔧 Reparación 1/3: 1 pedidos movidos
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 21 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 14 {'cambio_camion': 5, 'cambio': 9}
🗃️ Incidente #16 registrado y almacenado en memoria larga
```

**Resultado:** `ok`

Ejemplos de avisos a clientes:
- (cliente 4, pedido 11, cambio_camion) Hola Librería Pluma, por un malentendido, su pedido #11 será entregado por otro camión. La entrega se realizará aproximadamente a las 11:00. Gracias por su comprensión.
- (cliente 9, pedido 20, cambio) Hola Laboratorio Andes,

Por un imprevisto operativo, su pedido #20 llegará a las 11:18 (antes 09:36). Gracias por su comprensión.

Transportes Cordillera.
- (cliente 2, pedido 17, cambio) Hola Farmacia Santa Rita,

Queremos disculparnos por el retraso en la entrega de su pedido #17. Ahora se espera que llegue a las 11:40, lo que es una hora más tarde de lo previsto. Gracias por su comprensión.

Transportes Cordillera.

## Evento 3: «A las 10:30 el cliente 2 (VIP) pide urgente el pedido 14 antes de las 12:00»

```text
📥 Evento recibido: «A las 10:30 el cliente 2 (VIP) pide urgente el pedido 14 antes de las 12:00»
🧠 Clasificado como vip_urgente (fuente: LLM) · pedido 14, cliente 2
📚 Memoria larga: incidente similar (similitud 0.759): «Laboratorio VIP pidió adelantar su pedido por una muestra con cadena de frío Resolución: Se adelantó el pedido…» → estrategia previa: priorizar_y_reordenar
📖 Política aplicable: 01_prioridad_clientes_vip.md
⏱️ Reloj simulado a 10:30; entregas ya realizadas: [6, 18, 12]
⭐ Pedido 14 sube a prioridad 4, hora límite 12:00; se reordena la ruta
🗺️ Plan calculado a las 10:30: 18 entregas en 4 camiones
⚠️ Validación: 2 violaciones (VENTANA)
🔧 Reparación 1/3: 2 pedidos movidos
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 18 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 14 {'vip': 1, 'cambio': 10, 'cambio_camion': 3}
🗃️ Incidente #17 registrado y almacenado en memoria larga
```

**Resultado:** `ok`

Ejemplos de avisos a clientes:
- (cliente 2, pedido 14, vip) Hola Farmacia Santa Rita,

Confirmamos la entrega prioritaria de su pedido #14. Estimada hacia las 12:00. Transporte Cordillera.

Gracias por su confianza en nosotros.
- (cliente 9, pedido 5, cambio) Hola Laboratorio Andes,

Queremos disculparnos por el retraso en su pedido #5. Ahora se despachará hacia las 12:18, en lugar de las 12:03. Gracias por su comprensión.

Transportes Cordillera.
- (cliente 2, pedido 17, cambio) Hola, Farmacia Santa Rita. Mi pedido #17 llegará a las 10:33 (antes 11:40). Gracias por su comprensión. Transportes Cordillera.

## Evento 4: «A las 12:30 cliente ausente en el pedido 11»

```text
📥 Evento recibido: «A las 12:30 cliente ausente en el pedido 11»
🧠 Clasificado como entrega_fallida (fuente: reglas (prevalecieron sobre el LLM)) · pedido 11
📚 Memoria larga: incidente similar (similitud 0.743): «Nadie recibió el pedido en la oficina, portería sin autorización Resolución: Se reintentó el mismo día con avi…» → estrategia previa: reintento_misma_jornada
📖 Política aplicable: 03_entregas_fallidas.md
⏱️ Reloj simulado a 12:30; entregas ya realizadas: [11, 20, 14, 5, 17, 16, 23, 4, 7]
📦 Entrega fallida del pedido 11 (intento 1/2)
🔁 Reintento el mismo día en ventana 13:30-15:30
🗺️ Plan calculado a las 12:30: 10 entregas en 4 camiones
✅ Validación: el plan cumple capacidad, ventanas y turnos
📝 Plan ejecutado: 10 asignaciones y 5 hojas de ruta generadas
✉️ Avisos redactados: 1 {'fallida_hoy': 1}
🗃️ Incidente #18 registrado y almacenado en memoria larga
🚨 Memoria corta: 3 replanificaciones hoy → aviso de inestabilidad al supervisor
```

**Resultado:** `escalated`

Ejemplos de avisos a clientes:
- (cliente 4, pedido 11, fallida_hoy) Hola, querido cliente. No pudimos entregar su pedido #11. Reintentaremos hoy a las 14:19. Gracias por su paciencia.

## Resumen verificable

```json
{
  "eventos_en_memoria": 4,
  "replans_hoy": 3,
  "camion3": "averiado"
}
```
