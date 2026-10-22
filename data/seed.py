"""Genera el mundo ficticio de Transportes Cordillera (reproducible, seed=42).

Uso:  python data/seed.py
Todos los datos (empresas, personas, patentes) son inventados.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config, db  # noqa: E402

TRUCKS = [
    # id, patente, capacidad kg, conductor
    (1, "AB-1201", 800, "Marta Rojas"),
    (2, "CD-3342", 1200, "Luis Pardo"),
    (3, "EF-5518", 1500, "Sandra Vega"),
    (4, "GH-7723", 2000, "Pedro Lagos"),
    (5, "IJ-9904", 3000, "Hugo Contreras"),
]

CLIENTS = [
    (1, "Ferretería El Tornillo", "normal"),
    (2, "Farmacia Santa Rita", "VIP"),
    (3, "Panadería La Espiga", "normal"),
    (4, "Librería Pluma", "normal"),
    (5, "Clínica Dental Sonrisa", "VIP"),
    (6, "Minimarket Don Lalo", "normal"),
    (7, "Taller Mecánico Eje", "normal"),
    (8, "Café Altura", "normal"),
    (9, "Laboratorio Andes", "VIP"),
    (10, "Boutique Marina", "normal"),
]

# (descripción, resolución, estrategia, tipo, camión, cliente)
HISTORIC_INCIDENTS = [
    ("El camión no arranca por batería descargada en zona Norte",
     "Se reasignaron las entregas pendientes a los camiones de mayor capacidad y se envió una grúa.",
     "reasignar_a_mayor_capacidad", "averia", 3, None),
    ("Camión con falla de frenos detectada antes de salir del depósito",
     "Se retiró el camión de la jornada y se repartieron sus pedidos entre los demás.",
     "reasignar_a_mayor_capacidad", "averia", 2, None),
    ("Pinchazo de neumático en ruta hacia zona Sur",
     "El conductor cambió el neumático; se reprogramó la ventana de dos pedidos con aviso al cliente.",
     "avisar_y_ajustar_ventana", "averia", 4, None),
    ("Cliente ausente en la dirección de entrega, local cerrado",
     "Se reprogramó la entrega para el día siguiente en la mañana.",
     "reprogramar_manana", "entrega_fallida", None, 6),
    ("Nadie recibió el pedido en la oficina, portería sin autorización",
     "Se reintentó el mismo día con aviso previo al cliente y fue exitoso.",
     "reintento_misma_jornada", "entrega_fallida", None, 3),
    ("Cliente rechazó el pedido por embalaje dañado",
     "Se escaló al supervisor para gestionar la reposición.",
     "escalar_supervisor", "entrega_fallida", None, 7),
    ("Cliente ausente por segunda vez en el mismo pedido",
     "Se escaló al supervisor según la política de dos intentos.",
     "escalar_supervisor", "entrega_fallida", None, 6),
    ("Farmacia VIP solicitó entrega urgente de medicamentos antes del mediodía",
     "Se subió la prioridad al máximo y el pedido pasó al inicio de la ruta del camión más cercano.",
     "priorizar_y_reordenar", "vip_urgente", None, 2),
    ("Laboratorio VIP pidió adelantar su pedido por una muestra con cadena de frío",
     "Se adelantó el pedido y se avisó a los clientes desplazados.",
     "priorizar_y_reordenar", "vip_urgente", None, 9),
    ("Clínica VIP necesita insumos antes de una cirugía programada",
     "Se priorizó el pedido y se reordenó la ruta del camión cercano.",
     "priorizar_y_reordenar", "vip_urgente", None, 5),
    ("Choque leve del camión en zona Centro, sin heridos",
     "Se reasignaron los pedidos restantes y se levantó el parte del siniestro.",
     "reasignar_a_mayor_capacidad", "averia", 1, None),
    ("Sobrecalentamiento del motor en subida al Oriente",
     "Se esperó el enfriamiento y se avisó el retraso a los clientes de la ruta.",
     "avisar_y_ajustar_ventana", "averia", 5, None),
    ("Dirección incorrecta en el pedido, el cliente no fue ubicado",
     "Se llamó al cliente, se corrigió la dirección y se reprogramó para el día siguiente.",
     "reprogramar_manana", "entrega_fallida", None, 10),
    ("Cliente reportó que nadie estaba para recibir, repartidor esperó 15 minutos",
     "Se reintentó en la tarde del mismo día con confirmación telefónica.",
     "reintento_misma_jornada", "entrega_fallida", None, 8),
    ("Cliente VIP solicita adelantar entrega por falta de stock en su local",
     "Se reordenó la ruta para atender primero al cliente VIP.",
     "priorizar_y_reordenar", "vip_urgente", None, 2),
]


def build():
    rnd = random.Random(42)
    db.init_schema(reset=True)
    with db.connect() as c:
        for tid, plate, cap, driver in TRUCKS:
            c.execute("INSERT INTO trucks VALUES (?,?,?,?,?,?,?)",
                      (tid, plate, cap, "disponible", driver, db.DEPOT_ZONE, config.SHIFT_END))
        for cid, name, tier in CLIENTS:
            c.execute("INSERT INTO clients VALUES (?,?,?,?,?)",
                      (cid, name, tier, f"contacto{cid}@ejemplo.cl", ""))

        zones = [z for z in db.ZONES if z != "Industrial"] + ["Industrial"]
        for oid in range(1, 26):
            # los pedidos 14 y 8 se fijan para los escenarios de demo
            client = {14: 2, 8: 6, 3: 5, 20: 9, 11: 4}.get(oid, rnd.randint(1, 10))
            zone = {14: "Centro", 8: "Sur"}.get(oid, rnd.choice(zones))
            weight = rnd.choice([40, 60, 80, 120, 150, 200, 260, 320, 400])
            priority = 3 if client in (2, 5, 9) else rnd.choice([1, 2, 2, 3])
            start = rnd.choice([8, 9, 10, 11, 12, 13, 14]) * 60
            length = rnd.choice([120, 150, 180, 240])
            end = min(start + length, 17 * 60 + 30)
            if oid == 14:  # pedido VIP con ventana tarde, luego se pide urgencia
                start, end = 13 * 60, 16 * 60
            c.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,0)",
                      (oid, client, zone, weight, priority, start, end, "pendiente"))

        for i, (desc, res, strat, typ, truck, client) in enumerate(HISTORIC_INCIDENTS, 1):
            c.execute(
                "INSERT INTO incidents(ts,type,truck_id,order_id,client_id,description,resolution,strategy)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (f"2026-10-{(i % 20) + 1:02d} 10:00", typ, truck, None, client, desc, res, strat))
    db.set_now(config.SHIFT_START)
    return db.config.db_path()


if __name__ == "__main__":
    path = build()
    print(f"Base de datos creada en {path}")
    n = db.one("SELECT COUNT(*) n FROM orders")["n"]
    print(f"{len(TRUCKS)} camiones, {len(CLIENTS)} clientes, {n} pedidos, "
          f"{len(HISTORIC_INCIDENTS)} incidentes históricos")
