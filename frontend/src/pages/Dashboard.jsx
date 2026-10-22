import { useState } from "react";
import {
  KpiCard, KpiBars, ProgressBar, Card, ChartCard, ColumnChart, DonutChart, Field, Input, Button, Notice,
  List, ListRow, EmptyState, Spinner, DataTable, EntityCell, Badge, Eyebrow, Icon,
} from "../components";
import { parseLog, QUICK_EVENTS, EVENT_LABEL, kg, clientName, plural, resultTitle } from "../lib";

function Console({ busy, onEvent, result }) {
  const [text, setText] = useState("");
  const submit = (e) => {
    e.preventDefault();
    if (text.trim()) { onEvent(text); setText(""); }
  };
  const out = result && resultTitle(result);
  const cls = result?.classification;
  return (
    <Card title="Consola de eventos" action={<Badge tone="accent">Lenguaje natural</Badge>}>
      <form className="composer" onSubmit={submit}>
        <div className="composer__row">
          <Field label="Describe lo que ocurrió en la operación">
            <Input icon="chat" value={text} onChange={(e) => setText(e.target.value)} disabled={busy}
              placeholder="Ej.: A las 15:00 el camión 2 se averió" maxLength={500} />
          </Field>
          <Button type="submit" icon="send" disabled={busy || !text.trim()}>{busy ? "Razonando…" : "Enviar al agente"}</Button>
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          <Eyebrow>Escenarios rápidos</Eyebrow>
          <div className="quick-row">
            {QUICK_EVENTS.map((q) => (
              <Button key={q.label} type="button" variant="soft" size="sm" icon={q.icon} disabled={busy} onClick={() => onEvent(q.text)}>{q.label}</Button>
            ))}
          </div>
        </div>
      </form>
      {result && (
        <div style={{ display: "grid", gap: 10, marginTop: 16 }}>
          <Notice icon={out.icon} title={out.title}
            text={result.needs_info ?? `${EVENT_LABEL[cls?.tipo] ?? "Evento"} · ${cls?.source?.startsWith("llm") ? "clasificado por LLM" : "clasificado por reglas"} · ${result.seconds} s`} />
          {result.notifications?.length > 0 && (
            <span className="fx-row__sub">{plural(result.notifications.length, "aviso redactado", "avisos redactados")} · {plural(result.violations?.length ?? 0, "violación", "violaciones")} tras la última validación</span>
          )}
        </div>
      )}
    </Card>
  );
}

function Reasoning({ result, busy }) {
  const lines = result?.log?.map(parseLog) ?? [];
  return (
    <Card title="Razonamiento del agente" action={result && <Badge tone="neutral">{lines.length} pasos</Badge>}>
      {busy ? (
        <EmptyState icon="sparkle" title="El agente está razonando…" text="Clasifica el evento, consulta su memoria, planifica y valida el plan." action={<Spinner />} />
      ) : lines.length === 0 ? (
        <EmptyState icon="sparkle" title="Aún no hay eventos" text="Envía un evento o elige un escenario rápido para ver el razonamiento paso a paso." />
      ) : (
        <div className="log-scroll" aria-live="polite">
          {lines.map((l, i) => (
            <div key={i} className="log-line" data-tone={l.tone}>
              <span className="log-line__icon"><Icon name={l.icon} size={16} /></span>
              <span className="log-line__text">{l.text}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default function Dashboard({ ov, result, busy, onEvent, goto }) {
  const k = ov.kpis;
  const total = ov.orders.length;
  const nameOf = (id) => clientName(ov, id);
  const fleetRows = ov.fleet.map((t) => ({ ...t, key: t.id }));

  return (
    <>
      <div className="page-title">
        <h1 className="fx-h2" style={{ fontSize: 28 }}>Centro de control</h1>
        <p className="fx-lead" style={{ fontSize: 14 }}>
          Jornada {ov.clock.jornada} · reloj simulado {ov.clock.hm} · {k.trucks_ok} de {k.trucks_total} camiones operativos
        </p>
      </div>

      <div className="fx-kpis">
        <KpiCard highlight icon="doc" label="Entregas pendientes" value={k.pending} onOpen={() => goto("orders")}>
          <KpiBars light data={ov.fleet.map((t) => t.pending_stops || 0.2)} />
          <small style={{ opacity: 0.85 }}>{k.delivered} entregadas hoy · {k.at_risk} en riesgo</small>
        </KpiCard>
        <KpiCard icon="car" label="Camiones operativos" value={`${k.trucks_ok}/${k.trucks_total}`} onOpen={() => goto("routes")}>
          <ProgressBar value={k.utilization} left={`${k.utilization}%`} right="utilización de carga" label="Utilización de la flota" />
        </KpiCard>
        <KpiCard icon="refresh" label="Replanificaciones hoy" value={k.replans} onOpen={() => goto("memory")}>
          <ProgressBar value={Math.min(k.replans, 3)} max={3} left={`${k.replans} de 3`} right="umbral de aviso" label="Replanificaciones frente al umbral" />
        </KpiCard>
        <KpiCard icon="mail" label="Avisos a clientes" value={k.notifications} onOpen={() => goto("memory")}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Badge tone={k.escalations ? "danger" : "success"} dot>{plural(k.escalations, "escalamiento", "escalamientos")}</Badge>
            {k.failed + k.rescheduled > 0 && <Badge tone="warning">{plural(k.failed + k.rescheduled, "pedido con incidencia", "pedidos con incidencia")}</Badge>}
          </div>
        </KpiCard>
      </div>

      {ov.escalations.length > 0 && (
        <Notice icon="bell" title={`Escalado al supervisor: ${ov.escalations[0].summary}`} text={ov.escalations[0].recommendation} />
      )}

      <div className="fx-split">
        <Console busy={busy} onEvent={onEvent} result={result} />
        <Reasoning busy={busy} result={result} />
      </div>

      <section className="fx-table-wrap fx-table-wrap--dark" style={{ padding: 8 }}>
        <header className="table-note">
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}><strong style={{ fontSize: 18 }}>Flota</strong><Badge>{k.trucks_total} camiones</Badge></div>
          <Button variant="accent" size="sm" icon="arrow-right" onClick={() => goto("routes")}>Ver rutas</Button>
        </header>
        <DataTable dark rows={fleetRows} rowKey="id" columns={[
          { key: "truck", label: "Camión", render: (t) => <EntityCell name={`Camión ${t.id}`} sub={`${t.plate} · ${t.driver}`} avatarName={t.driver} dark /> },
          { key: "state", label: "Estado", render: (t) => <Badge tone={t.status === "averiado" ? "danger" : "success"} dot>{t.status === "averiado" ? "Averiado" : "Disponible"}</Badge> },
          { key: "load", label: "Carga", render: (t) => <span className="tnum">{kg(t.load_kg)} / {kg(t.capacity_kg)} · {t.utilization}%</span> },
          { key: "stops", label: "Paradas", align: "right", render: (t) => <span className="tnum">{t.pending_stops}</span> },
          { key: "zone", label: "Zona actual", render: (t) => t.current_zone },
        ]} />
      </section>

      <div className="fx-split">
        <ChartCard title="Carga asignada por camión" sub="Kilogramos pendientes de entregar por camión.">
          <ColumnChart ramp={false} color="var(--accent)" height={190}
            data={ov.fleet.map((t) => ({ label: `C${t.id}`, value: t.load_kg }))} />
        </ChartCard>
        <ChartCard title="Estado de los pedidos" sub="Distribución de los pedidos de la jornada.">
          <DonutChart total={String(total)} totalLabel="pedidos" items={[
            { label: "Por entregar", value: ov.order_counts.pendiente, color: "var(--accent)" },
            { label: "Entregados", value: ov.order_counts.entregado, color: "var(--success)" },
            { label: "Reprogramados", value: ov.order_counts.reprogramado, color: "var(--warning)" },
            { label: "Escalados", value: ov.order_counts.fallido, color: "var(--danger)" },
          ].filter((i) => i.value > 0)} />
        </ChartCard>
      </div>

      <Card title="Últimos avisos a clientes" action={<Badge tone="neutral">Envío simulado</Badge>}>
        {ov.outbox.length === 0 ? (
          <EmptyState icon="mail" title="Sin avisos todavía" text="Cuando el agente planifique o replanifique, los avisos aparecerán aquí." />
        ) : (
          <List variant="flat">
            {ov.outbox.slice(0, 6).map((m, i) => (
              <ListRow key={i} icon="mail" circle title={nameOf(m.client_id)}
                sub={<span className="clip">{m.message}</span>} side={m.order_id ? `Pedido #${m.order_id}` : ""} />
            ))}
          </List>
        )}
      </Card>
    </>
  );
}
