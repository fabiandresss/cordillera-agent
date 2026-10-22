# Política de capacidad de carga
Ningún camión puede cargar más peso que su capacidad nominal. La capacidad se mide en kilogramos y es una restricción dura: el planificador nunca asigna un pedido que exceda la capacidad restante del camión. Los pedidos que no caben en ningún camión se informan como no asignables y se escalan al supervisor.
Se recomienda repartir la carga de forma balanceada: ante empate entre camiones, se prefiere el que tiene menos carga asignada.
