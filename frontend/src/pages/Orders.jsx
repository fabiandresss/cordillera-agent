import { useMemo, useState } from "react";
import { SearchBar, FilterChips, DataTable, EntityCell, Badge, Card, Tile, List, ListRow, EmptyState, ProgressBar } from "../components";
import { ORDER_STATUS, kg } from "../lib";

const FILTERS = [
  { value: "all", label: "Todos" },
  { value: "open", label: "Por entregar" },
  { value: "entregado", label: "Entregados" },
  { value: "reprogramado", label: "Reprogramados" },
  { value: "fallido", label: "Escalados" },
];

export default function OrdersPage({ ov }) {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all");
  const [sel, setSel] = useState(14);

  const rows = useMemo(() => ov.orders.filter((o) => {
    const byStatus = filter === "all" || (filter === "open" ? ["pendiente", "asignado"].includes(o.status) : o.status === filter);
    const t = q.trim().toLowerCase();
    return byStatus && (!t || o.client_name.toLowerCase().includes(t) || String(o.id) === t || o.zone.toLowerCase().includes(t));
  }), [ov.orders, q, filter]);

  const order = ov.orders.find((o) => o.id === sel);
  const slack = order && order.eta != null ? order.window_end - order.eta : null;

  return (
    <>
      <div className="page-title">
        <h1 className="fx-h2" style={{ fontSize: 28 }}>Pedidos</h1>
        <p className="fx-lead" style={{ fontSize: 14 }}>Los {ov.orders.length} pedidos de la jornada, con su camión, ETA y estado actual.</p>
      </div>

      <div style={{ display: "grid", gap: 12 }}>
        <SearchBar placeholder="Buscar por cliente, zona o número de pedido…" value={q} onChange={(e) => setQ(e.target.value)} />
        <FilterChips options={FILTERS} value={filter} onChange={setFilter} variant="ink" />
      </div>

      <div className="split-wide">
        {rows.length === 0 ? (
          <Card><EmptyState icon="search" title="Sin resultados" text="Prueba con otro filtro o término de búsqueda." /></Card>
        ) : (
          <DataTable rows={rows} selected={sel} onSelect={setSel} columns={[
            { key: "id", label: "Pedido", render: (o) => <EntityCell name={`#${o.id}`} sub={o.zone} avatarName={o.client_name} /> },
            { key: "client", label: "Cliente", render: (o) => <span>{o.client_name} {o.tier === "VIP" && <Badge tone="accent">VIP</Badge>}</span> },
            { key: "eta", label: "ETA", render: (o) => <span className={`tnum ${o.at_risk ? "fx-delta" : ""}`} data-dir={o.at_risk ? "down" : undefined}>{o.eta_hm ?? "—"}</span> },
            { key: "truck", label: "Camión", render: (o) => (o.truck_id ? `C${o.truck_id}` : "—") },
            { key: "status", label: "Estado", render: (o) => { const s = ORDER_STATUS[o.status] ?? { label: o.status, tone: "neutral" }; return <Badge tone={s.tone} dot>{s.label}</Badge>; } },
          ]} />
        )}

        {order && (
          <Card title={`Pedido #${order.id}`} action={order.tier === "VIP" ? <Badge tone="accent">Cliente VIP</Badge> : <Badge>Cliente normal</Badge>}>
            <div style={{ display: "grid", gap: 16 }}>
              <div>
                <strong style={{ fontSize: 18 }}>{order.client_name}</strong>
                <div className="fx-row__sub">Zona {order.zone} · {kg(order.weight_kg)}</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                <Tile value={`P${order.priority}`} label="Prioridad (4 = urgente)" ink={order.priority >= 4} />
                <Tile value={order.attempts} label="Intentos fallidos" />
              </div>
              <List variant="flat">
                <ListRow icon="clock" circle title="Ventana de entrega" amount={order.window} />
                <ListRow icon="car" circle title="Camión asignado" amount={order.truck_id ? `Camión ${order.truck_id}` : "Sin asignar"} />
                <ListRow icon="pin" circle title="Hora estimada (ETA)" amount={order.eta_hm ?? "—"} side={order.at_risk ? "Fuera de ventana" : order.eta_hm ? "Dentro de ventana" : ""} />
              </List>
              {slack != null && (
                <ProgressBar value={Math.max(0, Math.min(slack, 120))} max={120} left={slack >= 0 ? `${slack} min de holgura` : `${Math.abs(slack)} min de atraso`}
                  right="holgura vs. cierre" label="Holgura de la ventana" />
              )}
            </div>
          </Card>
        )}
      </div>
    </>
  );
}
