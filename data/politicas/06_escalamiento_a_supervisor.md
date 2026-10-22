# Política de escalamiento al supervisor
Se escala al supervisor de operaciones cuando: el evento no se puede clasificar, falta información crítica, un pedido acumula dos intentos fallidos, ningún camión puede cumplir la ventana de un pedido después de tres intentos de reparación del plan, o la jornada acumula tres o más replanificaciones, lo que indica inestabilidad operativa.
El escalamiento genera una nota con el resumen del problema, las acciones ya intentadas y la recomendación del agente. El agente nunca cancela pedidos por su cuenta.
