/* Utilidades de presentación: mapean datos del agente a los componentes del kit. */

/** Emoji inicial de cada línea del log del agente → icono del kit. */
const LOG_ICONS = [
  ["📥", "download"], ["🧠", "sparkle"], ["📚", "history"], ["📖", "doc"], ["⏱", "clock"],
  ["🔧", "settings"], ["🗓", "calendar"], ["⭐", "star"], ["📦", "swap"], ["🔁", "refresh"],
  ["📅", "calendar"], ["🚨", "bell"], ["🗺", "compass"], ["✅", "check"], ["⚠", "info"],
  ["📝", "file-plus"], ["✉", "mail"], ["🗃", "save"], ["❓", "info"], ["ℹ", "info"],
];

export function parseLog(line) {
  const text = line.replace(/\*\*/g, "");
  const hit = LOG_ICONS.find(([e]) => text.startsWith(e));
  const body = hit ? text.slice(hit[0].length).replace(/^️/, "").trim() : text;
  const tone = /🚨|⚠/.test(text.slice(0, 3)) ? "warn" : /✅/.test(text.slice(0, 2)) ? "ok" : "";
  return { icon: hit ? hit[1] : "info", text: body, tone };
}

export const EVENT_LABEL = {
  nuevo_dia: "Inicio de jornada", averia: "Avería", vip_urgente: "VIP urgente",
  entrega_fallida: "Entrega fallida", otro: "No reconocido", desconocido: "Evento",
};
export const EVENT_ICON = {
  nuevo_dia: "calendar", averia: "bolt", vip_urgente: "crown", entrega_fallida: "swap", otro: "info",
};
export const EVENT_TONE = { nuevo_dia: "info", averia: "danger", vip_urgente: "accent", entrega_fallida: "warning", otro: "neutral" };

export const ORDER_STATUS = {
  pendiente: { label: "Pendiente", tone: "warning" },
  asignado: { label: "Asignado", tone: "info" },
  entregado: { label: "Entregado", tone: "success" },
  reprogramado: { label: "Reprogramado", tone: "accent" },
  fallido: { label: "Escalado", tone: "danger" },
};

export const OUTCOME = {
  ok: { icon: "check", title: "Plan actualizado", tone: "success" },
  escalated: { icon: "bell", title: "Escalado al supervisor", tone: "danger" },
  needs_info: { icon: "info", title: "El agente necesita más datos", tone: "warning" },
  sin_accion: { icon: "info", title: "Sin cambios en el plan", tone: "neutral" },
};

export const HISTORY_OUTCOME = { ok: "Completado", escalated: "Escalado", needs_info: "Faltan datos", sin_accion: "Sin cambios" };

export const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

export const kg = (n) => `${Number(n).toLocaleString("es-CL")} kg`;

export const QUICK_EVENTS = [
  { icon: "calendar", label: "Inicio de jornada", text: "Inicio de jornada" },
  { icon: "bolt", label: "Avería camión 3", text: "A las 11:00 el camión 3 se averió en la Zona Norte" },
  { icon: "crown", label: "VIP urgente", text: "A las 10:00 el cliente 2 (VIP) necesita su pedido 14 antes de las 12:00" },
  { icon: "swap", label: "Entrega fallida", text: "A las 10:00 cliente ausente en el pedido 11" },
  { icon: "history", label: "Segundo fallo", text: "A las 13:00 nuevamente ausente en el pedido 11, nadie lo recibió" },
  { icon: "info", label: "Evento ambiguo", text: "No funciona nada!" },
];

export function clientName(ov, id) {
  return ov.orders.find((o) => o.client_id === id)?.client_name ?? `Cliente ${id}`;
}

const DECISION_TITLE = {
  fallida_manana: { icon: "calendar", title: "Entrega reprogramada para mañana", tone: "warning" },
  fallida_hoy: { icon: "refresh", title: "Reintento de entrega el mismo día", tone: "success" },
  fallida_escalada: { icon: "bell", title: "Pedido escalado al supervisor", tone: "danger" },
  averia: { icon: "check", title: "Camión retirado y pedidos reasignados", tone: "success" },
  vip: { icon: "crown", title: "Pedido priorizado y ruta reordenada", tone: "success" },
  nuevo_dia: { icon: "check", title: "Jornada planificada", tone: "success" },
};

/** Título del resultado de un evento: prioriza la decisión concreta sobre el estado genérico. */
export function resultTitle(result) {
  if (result.outcome === "needs_info" || result.outcome === "sin_accion") return OUTCOME[result.outcome];
  const d = DECISION_TITLE[result.decision?.kind];
  if (d && result.outcome === "ok") return d;
  if (d && result.outcome === "escalated" && result.decision.kind === "fallida_escalada") return d;
  return OUTCOME[result.outcome] ?? OUTCOME.sin_accion;
}
