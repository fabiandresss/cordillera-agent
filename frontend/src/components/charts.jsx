import { useId } from "react";
import { cx } from "./primitives.jsx";

/* Columnas gruesas redondeadas (estilo shadcn "Contribution History").
   ramp: las barras van de gris claro a ink según su posición (como la referencia).
   data: [{label, value}] */
export function ColumnChart({ data, height = 200, ramp = true, color = "var(--ink)" }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="fx-columns" style={{ height }} role="img" aria-label={data.map((d) => `${d.label}: ${d.value}`).join(", ")}>
      {data.map((d, k) => (
        <div key={d.label} className="fx-columns__col">
          <div className="fx-columns__bar" style={{
            height: `${(d.value / max) * 100}%`,
            background: ramp ? `color-mix(in srgb, ${color} ${25 + (75 * k) / Math.max(1, data.length - 1)}%, var(--surface-mute))` : color,
          }} />
          <span className="fx-columns__label">{d.label}</span>
        </div>
      ))}
    </div>
  );
}

/* Barras agrupadas (ingresos vs gastos). series: [{key, label, color}] ; data: [{label, [key]: n}] */
export function GroupedBarChart({ data, series, height = 200 }) {
  const max = Math.max(...data.flatMap((d) => series.map((s) => d[s.key])), 1);
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="fx-legend">{series.map((s) => <span key={s.key}><i style={{ background: s.color }} />{s.label}</span>)}</div>
      <div className="fx-grouped" style={{ height }} role="img" aria-label="Gráfico de barras agrupadas">
        {data.map((d) => (
          <div key={d.label} style={{ display: "grid", gridTemplateRows: "1fr auto", gap: 8, height: "100%" }}>
            <div className="fx-grouped__col">
              {series.map((s) => <span key={s.key} className="fx-grouped__bar" style={{ height: `${(d[s.key] / max) * 100}%`, background: s.color }} title={`${s.label}: ${d[s.key]}`} />)}
            </div>
            <span className="fx-columns__label" style={{ textAlign: "center" }}>{d.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* Línea suave con área degradada. Para KPIs (Average Payment Time / Available Balance) */
export function Sparkline({ data, width = 220, height = 56, color = "var(--accent)", dots = false, area = true }) {
  const id = useId().replace(/:/g, "");
  const max = Math.max(...data), min = Math.min(...data);
  const pts = data.map((v, k) => [(k / (data.length - 1)) * width, height - 4 - ((v - min) / (max - min || 1)) * (height - 8)]);
  const d = pts.map((p, k) => {
    if (!k) return `M${p[0]},${p[1]}`;
    const [px, py] = pts[k - 1];
    const cx1 = px + (p[0] - px) / 2;
    return `C${cx1},${py} ${cx1},${p[1]} ${p[0]},${p[1]}`;
  }).join(" ");
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true" style={{ overflow: "visible", color }}>
      <defs><linearGradient id={id} x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="currentColor" stopOpacity=".18" /><stop offset="1" stopColor="currentColor" stopOpacity="0" /></linearGradient></defs>
      {area && <path d={`${d} L${width},${height} L0,${height} Z`} fill={`url(#${id})`} />}
      <path d={d} fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" />
      {dots && pts.map(([x, y], k) => <circle key={k} cx={x} cy={y} r="3" fill="var(--surface)" stroke="currentColor" strokeWidth="1.5" />)}
    </svg>
  );
}

/* Barras pequeñas para dentro de un KPI. light = barras blancas translúcidas (KPI destacado) */
export function KpiBars({ data, height = 52, light, color = "var(--accent)" }) {
  const max = Math.max(...data, 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height }} aria-hidden="true">
      {data.map((v, k) => (
        <span key={k} style={{ flex: 1, height: `${(v / max) * 100}%`, borderRadius: 4, background: light ? "rgba(255,255,255,.55)" : `color-mix(in srgb, ${color} 45%, transparent)` }} />
      ))}
    </div>
  );
}

/* Donut con total al centro y leyenda con % y monto. items: [{label, value, color, display?}] */
export function DonutChart({ items, size = 160, thickness = 22, total, totalLabel = "Total" }) {
  const sum = items.reduce((a, b) => a + b.value, 0);
  const r = (size - thickness) / 2, c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="fx-donut">
      <div className="fx-donut__chart" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(-90deg)" }} aria-hidden="true">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-mute)" strokeWidth={thickness} />
          {items.map((it) => {
            const len = (it.value / sum) * c;
            const el = <circle key={it.label} cx={size / 2} cy={size / 2} r={r} fill="none" stroke={it.color} strokeWidth={thickness} strokeDasharray={`${Math.max(0, len - 3)} ${c}`} strokeDashoffset={-offset} strokeLinecap="round" />;
            offset += len;
            return el;
          })}
        </svg>
        <div className="fx-donut__center"><strong>{total}</strong><small>{totalLabel}</small></div>
      </div>
      <div className="fx-donut__legend">
        {items.map((it) => (
          <div key={it.label}><i style={{ background: it.color }} /><span>{it.label}</span><span className="fx-row__sub">{Math.round((it.value / sum) * 100)}%</span><strong style={{ fontWeight: 500 }}>{it.display ?? it.value}</strong></div>
        ))}
      </div>
    </div>
  );
}

/* Contenedor con título + subtítulo + acción para cualquier gráfico */
export function ChartCard({ title, sub, action, className, children }) {
  return (
    <section className={cx("fx-card", className)}>
      <header className="fx-card__head">
        <div><h3 className="fx-card__title" style={{ fontSize: 17, fontWeight: 600 }}>{title}</h3>{sub && <div className="fx-row__sub" style={{ fontSize: 13 }}>{sub}</div>}</div>
        {action}
      </header>
      {children}
    </section>
  );
}
