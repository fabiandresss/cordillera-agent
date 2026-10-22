import { useState } from "react";
import {
  Tabs, Card, Notice, Tile, List, ListRow, DataTable, Badge, SearchBar, ProgressBar, EmptyState, Button, Spinner, Eyebrow,
} from "../components";
import { api } from "../api";
import { EVENT_LABEL, EVENT_ICON, EVENT_TONE, HISTORY_OUTCOME } from "../lib";

const SUGGESTIONS = ["se me rompió una rueda del camión", "cliente ausente en la dirección", "farmacia pide entrega urgente"];

function Search() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const run = async (text) => {
    const term = (text ?? q).trim();
    if (term.length < 2) return;
    setQ(term);
    setBusy(true);
    setErr(null);
    try { setHits(await api.search(term)); } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <Card title="Búsqueda semántica en la memoria larga" action={<Badge tone="accent">ChromaDB · coseno</Badge>}>
      <div style={{ display: "grid", gap: 14 }}>
        <form onSubmit={(e) => { e.preventDefault(); run(); }} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 220 }}><SearchBar placeholder="Describe un problema con tus palabras…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
          <Button type="submit" icon="search" disabled={busy || q.trim().length < 2}>Buscar</Button>
        </form>
        <div className="quick-row">
          {SUGGESTIONS.map((s) => <Button key={s} type="button" variant="soft" size="sm" onClick={() => run(s)}>{s}</Button>)}
        </div>
        {err && <Notice icon="info" title="No se pudo buscar" text={err} />}
        {busy ? <div style={{ display: "grid", placeItems: "center", padding: 24 }}><Spinner /></div> : hits && (hits.length === 0 ? (
          <EmptyState icon="search" title="Sin coincidencias" text="Ningún incidente se parece lo suficiente." />
        ) : (
          <List variant="flat">
            {hits.map((h, i) => (
              <li key={i} className="fx-row" style={{ display: "grid", gap: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                  <Badge tone={EVENT_TONE[h.metadata.type] ?? "neutral"}>{EVENT_LABEL[h.metadata.type] ?? h.metadata.type}</Badge>
                  <Badge tone="neutral">{h.metadata.strategy || "sin estrategia"}</Badge>
                </div>
                <div style={{ fontSize: 14, lineHeight: 1.5 }}>{h.text}</div>
                <ProgressBar value={Math.round(h.score * 100)} left={`${Math.round(h.score * 100)}% de similitud`} right="umbral de aceptación: 60%" label="Similitud" />
              </li>
            ))}
          </List>
        ))}
      </div>
    </Card>
  );
}

export default function MemoryPage({ ov }) {
  const [tab, setTab] = useState("short");
  return (
    <>
      <div className="page-title">
        <h1 className="fx-h2" style={{ fontSize: 28 }}>Memoria del agente</h1>
        <p className="fx-lead" style={{ fontSize: 14 }}>Corta: lo que ocurrió en esta jornada. Larga: incidentes pasados que el agente recuerda por significado.</p>
      </div>
      <Tabs value={tab} onChange={setTab} tabs={[
        { value: "short", label: "Memoria corta" }, { value: "long", label: "Memoria larga" }, { value: "search", label: "Búsqueda semántica" },
      ]} />

      {tab === "short" && (
        <div className="fx-split" style={{ alignItems: "start" }}>
          <div style={{ display: "grid", gap: 16 }}>
            <Notice icon="info" title="Continuidad de la jornada"
              text={`Checkpointer SQLite de LangGraph · thread «${ov.thread_id}». Si el servidor se reinicia, el agente retoma el estado.`} />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
              <Tile value={ov.history.length} label="Eventos en memoria" />
              <Tile ink value={`${ov.kpis.replans} / 3`} label="Replanificaciones hoy" />
            </div>
          </div>
          <Card title="Eventos de la jornada" action={<Badge>{ov.history.length}</Badge>}>
            {ov.history.length === 0 ? (
              <EmptyState icon="history" title="Memoria vacía" text="Envía un evento desde el Centro de control." />
            ) : (
              <List variant="flat">
                {[...ov.history].reverse().map((h, i) => (
                  <ListRow key={i} circle icon={EVENT_ICON[h.evento] ?? "info"} title={EVENT_LABEL[h.evento] ?? h.evento}
                    sub={[h.camion && `Camión ${h.camion}`, h.pedido && `Pedido #${h.pedido}`].filter(Boolean).join(" · ") || "Sin referencias"}
                    amount={h.hora} side={HISTORY_OUTCOME[h.resultado] ?? h.resultado} />
                ))}
              </List>
            )}
          </Card>
        </div>
      )}

      {tab === "long" && (
        <section className="fx-table-wrap" style={{ padding: 8 }}>
          <header className="table-note"><strong style={{ fontSize: 18 }}>Incidentes registrados</strong><Badge>{ov.incidents.length} recientes</Badge></header>
          <DataTable rows={ov.incidents} columns={[
            { key: "type", label: "Tipo", render: (r) => <Badge tone={EVENT_TONE[r.type] ?? "neutral"}>{EVENT_LABEL[r.type] ?? r.type}</Badge> },
            { key: "description", label: "Descripción", render: (r) => <span className="clip" style={{ maxWidth: 420 }}>{r.description}</span> },
            { key: "strategy", label: "Estrategia", render: (r) => r.strategy || "—" },
            { key: "ts", label: "Fecha", render: (r) => <span className="tnum">{r.ts}</span> },
          ]} />
        </section>
      )}

      {tab === "search" && <Search />}
      <Eyebrow>Cada incidente nuevo se indexa al registrarse y queda disponible para la misma jornada.</Eyebrow>
    </>
  );
}
