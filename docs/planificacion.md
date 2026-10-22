# Planificación y toma de decisiones (src/planner.py)

La prioridad, la asignación y la validación viven en código determinista, verificable con tests.
El LLM interpreta texto libre y redacta avisos, pero **no decide prioridades**.

## Parámetros (src/config.py)
| Parámetro | Valor |
|---|---|
| Jornada | 08:00–18:00 |
| Servicio por parada | 10 min |
| Velocidad base | 40 km/h × multiplicador de tráfico por zona y franja (`data/traffic.json`) |
| Máximo de intentos de entrega | 2 |
| Reparaciones antes de escalar | 3 |
| Umbral de similitud semántica | 0.60 (coseno) |

## 1. Puntuación de urgencia
```
holgura = cierre_ventana − ahora − viaje(depósito → zona)
score   = prioridad × 100 + (50 si cliente VIP) + 100 / max(holgura, 5)
```
Los pedidos se ordenan por `score` descendente. Prioridad 1–3 base; 4 = urgencia VIP.

## 2. Asignación (fase A)
Para cada pedido, en orden de `score`, se consideran los camiones con capacidad restante suficiente
(restricción dura). Se elige el de menor costo:
```
costo = km(última zona del camión → zona del pedido) − 3 (si ya estaba en ese camión) + 0.002 × carga
```
El término `−3` da **estabilidad**: un replan casi no mueve pedidos que no lo necesitan.
Los pedidos que no caben en ningún camión quedan como `sin_capacidad` y se escalan.

## 3. Secuenciación (fase B)
Dentro de cada camión se elige iterativamente el pedido de menor clave:
```
clave = cierre_ventana + 2 × viaje − 60 × (prioridad − 1) − 30 (si VIP)
```
y se simulan los ETA: `eta = max(llegada, apertura_ventana)`. Se marca `late` si `eta > cierre` y
`over_shift` si la parada termina después del fin de turno.

## 4. Validación y reparación
`validate_plan` devuelve violaciones tipadas: `CAPACIDAD`, `VENTANA`, `TURNO`.
`repair` mueve pedidos atrasados a otra posición u otro camión y acepta el movimiento solo si
**reduce el atraso total**. Si no hay mejora posible, el grafo escala sin insistir.

## 5. Decisiones por tipo de evento
| Evento | Decisión | Política |
|---|---|---|
| `nuevo_dia` | Planificar todos los pedidos abiertos | — |
| `averia` | Camión → averiado; reasignar sus pedidos pendientes; avisar a los afectados | 02 |
| `vip_urgente` | Prioridad 4 y hora límite; reordenar la ruta; avisar a los desplazados | 01 |
| `entrega_fallida` (1.er intento) | Reintento hoy si hay holgura; **mañana** si el cliente tiene ausencias previas (BD o memoria semántica) o no hay holgura | 03 |
| `entrega_fallida` (2.º intento) | Escalar al supervisor; no se reprograma solo | 03, 06 |
| `otro` | Escalar sin tocar el plan | 06 |
| dato faltante / id inexistente | Pedir el dato (no adivinar) | — |
| ≥ 3 replanificaciones en la jornada | Aviso de inestabilidad (memoria corta) | 06 |

## 6. Reloj simulado
Cada evento puede traer una hora («A las 11:00 …»). Al avanzarla, las entregas cuyo ETA ya pasó se
consideran realizadas; el replan parte de la posición real de cada camión (zona de su última entrega).
