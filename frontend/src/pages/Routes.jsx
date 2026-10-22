import { useState } from "react";
import { Tabs, StatStrip, Card, List, ListRow, Badge, EmptyState, Eyebrow, Notice } from "../components";
import { kg } from "../lib";

export default function RoutesPage({ ov }) {
  const [sel, setSel] = useState(String(ov.fleet[0]?.id ?? 1));
  const truck = ov.fleet.find((t) => String(t.id) === sel) ?? ov.fleet[0];
  const stops = ov.routes.find((r) => r.truck_id === truck.id)?.stops ?? [];
  const pending = stops.filter((s) => s.status === "planificado");
  const broken = truck.status === "averiado";
  const lastEta = pending.length ? pending[pending.length - 1].eta_hm : "—";
  const late = pending.filter((s) => s.eta > s.window_end).length;

  return (
    <>
      <div className="page-title">
        <h1 className="fx-h2" style={{ fontSize: 28 }}>Rutas y flota</h1>
        <p className="fx-lead" style={{ fontSize: 14 }}>Secuencia de entregas de cada camión, con hora estimada de llegada (ETA) y ventana del cliente.</p>
      </div>

      <Tabs value={sel} onChange={setSel}
        tabs={ov.fleet.map((t) => ({ value: String(t.id), label: `Camión ${t.id}${t.status === "averiado" ? " ⚠" : ""}` }))} />

      <div className="fx-split">
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
          <StatStrip
            stats={[
              { value: pending.length, label: "Paradas por hacer" },
              { value: kg(truck.load_kg), label: "Carga actual" },
              { value: lastEta, label: "Fin estimado", accent: true },
            ]}
            progress={truck.utilization}
            progressLabel={`${kg(truck.load_kg)} de ${kg(truck.capacity_kg)}`}
            progressAction={<Badge tone={broken ? "danger" : "success"} dot>{broken ? "Averiado" : "Disponible"}</Badge>}
          />
          <Card title={`${truck.plate}`} action={<Badge tone="neutral">{truck.driver}</Badge>}>
            <div className="kv"><Eyebrow>Zona actual</Eyebrow><strong>{truck.current_zone}</strong></div>
            <div className="kv"><Eyebrow>Capacidad</Eyebrow><strong>{kg(truck.capacity_kg)}</strong></div>
            <div className="kv"><Eyebrow>Riesgo de atraso</Eyebrow><strong>{late ? `${late} paradas fuera de ventana` : "Sin atrasos previstos"}</strong></div>
          </Card>
          {broken && <Notice icon="info" title="Camión fuera de servicio" text="Sus entregas pendientes fueron reasignadas a los demás camiones." />}
        </div>

        <Card title="Secuencia de entregas" action={<Badge>{stops.length} paradas</Badge>}>
          {stops.length === 0 ? (
            <EmptyState icon="car" title={broken ? "Camión averiado" : "Sin entregas asignadas"}
              text={broken ? "El agente reasignó sus pedidos pendientes." : "Planifica la jornada para ver su ruta."} />
          ) : (
            <List variant="flat">
              {stops.map((s) => {
                const done = s.status === "entregado";
                const isLate = !done && s.eta > s.window_end;
                return (
                  <ListRow key={s.order_id} circle accent={s.tier === "VIP" && !done}
                    icon={done ? "check" : s.tier === "VIP" ? "crown" : "pin"}
                    title={<>#{s.order_id} · {s.client_name}</>}
                    sub={`${s.zone} · ventana ${s.window} · ${kg(s.weight_kg)}`}
                    amount={s.eta_hm}
                    side={done ? "Entregado" : isLate ? "Fuera de ventana" : "Planificado"} />
                );
              })}
            </List>
          )}
        </Card>
      </div>
    </>
  );
}
