async function call(path, { method = "GET", body } = {}) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const j = await res.json();
      if (typeof j.detail === "string") detail = j.detail;
      else if (Array.isArray(j.detail)) detail = "Revisa el texto ingresado.";
    } catch { /* respuesta sin JSON */ }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  overview: () => call("/api/overview"),
  event: (text) => call("/api/events", { method: "POST", body: { text } }),
  reset: () => call("/api/reset", { method: "POST" }),
  provider: (provider) => call("/api/provider", { method: "POST", body: { provider } }),
  search: (q) => call(`/api/memory/search?q=${encodeURIComponent(q)}&k=5`),
  chat: (question) => call("/api/chat", { method: "POST", body: { question } }),
};
