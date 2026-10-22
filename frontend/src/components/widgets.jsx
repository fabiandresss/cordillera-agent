import { useState } from "react";
import { cx, Icon, Avatar, Switch } from "./primitives.jsx";
import { Delta, ProgressBar, StatusBadge } from "./feedback.jsx";
import { Photo, AvatarStack } from "./media.jsx";

/* ---------- Admin ---------- */

/* KPI con icono, flecha, valor, variación y un gráfico opcional (children).
   highlight = tarjeta rellena con el gradiente de marca (la métrica principal, solo una por fila) */
export function KpiCard({ icon, label, value, delta, deltaText = "from last month", highlight, children, onOpen }) {
  return (
    <article className={cx("fx-kpi", highlight && "fx-kpi--highlight")}>
      <div className="fx-kpi__head">
        <span className="fx-kpi__icon"><Icon name={icon} size={18} /></span>
        {label}
        <button className="fx-kpi__arrow" aria-label={`Abrir ${label}`} onClick={onOpen}><Icon name="arrow-up-right" size={14} /></button>
      </div>
      <p className="fx-kpi__value">{value}</p>
      {delta !== undefined && <Delta value={delta} suffix="%">{deltaText}</Delta>}
      {children}
    </article>
  );
}

/* Tabla de datos con selección de fila y badges de estado.
   columns: [{key, label, render?(row), align?}] ; dark = panel navy (FlowFin) */
export function DataTable({ columns, rows, rowKey = "id", selected, onSelect, dark, caption }) {
  return (
    <div className={cx("fx-table-wrap", dark && "fx-table-wrap--dark")}>
      <table className="fx-table">
        {caption && <caption className="fx-eyebrow" style={{ textAlign: "left", padding: "14px 12px 0" }}>{caption}</caption>}
        <thead><tr>{columns.map((c) => <th key={c.key} style={{ textAlign: c.align }}>{c.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r[rowKey]} aria-selected={selected === r[rowKey]} onClick={() => onSelect?.(r[rowKey])} tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && onSelect?.(r[rowKey])}>
              {columns.map((c) => <td key={c.key} style={{ textAlign: c.align }}>{c.render ? c.render(r) : c.key === "status" ? <StatusBadge status={r.status} /> : r[c.key]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* Celda "persona/empresa": avatar con inicial + título + subtítulo.
   avatarName = de quién sale la inicial si no es el título (p. ej. factura INV-1042 → cliente "Acme") */
export const EntityCell = ({ name, sub, src, dark, avatarName }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
    <Avatar src={src} name={avatarName ?? name} dark={dark} />
    <div><div style={{ fontWeight: 500 }}>{name}</div>{sub && <div className="fx-row__sub">{sub}</div>}</div>
  </div>
);

/* ---------- Móvil / servicios ---------- */

/* Cabecera de perfil grande: foto, nombre, teléfono, chip de membresía + acción */
export function ProfileHeader({ src, name, sub, badge, action }) {
  return (
    <div className="fx-profile">
      {src ? <img className="fx-profile__avatar" src={src} alt={name} /> : <span className="fx-profile__avatar" aria-hidden="true" />}
      <h1 className="fx-profile__name">{name}</h1>
      {sub && <div className="fx-row__sub" style={{ fontSize: 14 }}>{sub}</div>}
      {(badge || action) && <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginTop: 10 }}>{badge}{action}</div>}
    </div>
  );
}

/* Franja negra con 3 cifras separadas + barra de límite. stats: [{value, label, accent?}] */
export function StatStrip({ stats, progress, progressLabel, progressAction }) {
  return (
    <section className="fx-statstrip">
      <div className="fx-statstrip__row">
        {stats.map((s) => <div key={s.label}><strong className={s.accent ? "fx-accent-text" : undefined}>{s.value}</strong><small>{s.label}</small></div>)}
      </div>
      {progress !== undefined && (
        <div style={{ display: "grid", gap: 10 }}>
          <div className="fx-progress__track" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}><div className="fx-progress__fill" style={{ width: `${progress}%` }} /></div>
          <div className="fx-progress__meta"><span>{progressLabel}</span>{progressAction}</div>
        </div>
      )}
    </section>
  );
}

/* Tarjeta-acción grande en color de acento con flecha circular: "Book a ride" */
export const ActionCard = ({ title, sub, onClick, icon = "arrow-right" }) => (
  <button className="fx-actioncard" onClick={onClick}>
    <span><span className="fx-actioncard__title" style={{ display: "block" }}>{title}</span>{sub && <span className="fx-actioncard__sub">{sub}</span>}</span>
    <span className="fx-actioncard__go"><Icon name={icon} size={20} /></span>
  </button>
);

/* Mosaico de cifra (12 Rides taken / ★ 320 pts). ink = negro con valor en acento */
export const Tile = ({ value, label, ink, icon }) => (
  <div className={cx("fx-tile", ink && "fx-tile--ink")}>
    <strong>{icon && <Icon name={icon} size={18} fill="currentColor" style={{ verticalAlign: "-2px", marginRight: 6 }} />}{value}</strong>
    <small>{label}</small>
  </div>
);

/* Viaje/ruta: nivel en color, Origen → Destino, monto, fecha */
export const RouteCard = ({ tier, from, to, amount, when }) => (
  <article className="fx-route">
    {tier && <span className="fx-route__tier">{tier}</span>}
    <div className="fx-route__line">{from}<Icon name="arrow-right" size={16} />{to}<span className="fx-route__amount">{amount}</span></div>
    {when && <span className="fx-row__sub">{when}</span>}
  </article>
);

/* Meta de ahorro grupal: banda con gradiente/foto, chip de destino, saldo, miembros y progreso */
export function GoalCard({ title, icon = "plane", image, label = "Accumulated Balance", amount, goal, members = [], onOpen }) {
  const pct = Math.round((amount.value / goal.value) * 100);
  return (
    <article className="fx-goal">
      <div className="fx-goal__top">
        {image && <Photo src={image} alt="" />}
        <button className="fx-btn fx-btn--sm" style={{ background: "#111214", color: "#fff", width: "fit-content" }} onClick={onOpen}>
          <Icon name={icon} size={16} />{title}<Icon name="chevron" size={14} />
        </button>
        <div><div style={{ fontSize: 13, opacity: .9 }}>{label}</div><div style={{ fontSize: 34, fontWeight: 700, letterSpacing: "-0.03em" }}>{amount.display}</div></div>
        {members.length > 0 && (
          <div className="fx-goal__members">With{members.slice(0, 2).map((m) => <Avatar key={m.name} src={m.src} name={m.name} />)}{members.length > 2 && <span className="fx-avatars__more" style={{ background: "#2a2b2e", color: "#fff" }}>+{members.length - 2}</span>}</div>
        )}
      </div>
      <div className="fx-goal__bottom"><ProgressBar value={pct} left={`${pct}%`} right={`${amount.display} / ${goal.display}`} /></div>
    </article>
  );
}

/* Mini tarjeta de grupo/plan: imagen circular, título, miembros, progreso */
export const PlanTile = ({ image, title, sub, pct }) => (
  <article className="fx-card" style={{ padding: 12, display: "grid", gap: 8, minWidth: 130 }}>
    <Photo src={image} alt="" style={{ width: 52, height: 52, borderRadius: "50%" }} />
    <div><div style={{ fontSize: 13.5, fontWeight: 600 }}>{title}</div><div className="fx-row__sub">{sub}</div></div>
    <ProgressBar value={pct} right={`${pct}%`} />
  </article>
);

/* ---------- Wallet nocturno ---------- */

/* Tarjeta de pago metálica. variant: gold | diamond | platinum | accent */
export function PaymentCard({ variant = "platinum", name, last4, defaultActive = true }) {
  const [on, setOn] = useState(defaultActive);
  return (
    <article className={cx("fx-paycard", `fx-paycard--${variant}`)}>
      <div className="fx-paycard__top"><span>{name}</span><span>•••• {last4}</span></div>
      <div className="fx-paycard__bottom">
        <div className="fx-paycard__tools">
          <button aria-label="Congelar"><Icon name="snow" size={16} /></button>
          <button aria-label="Detalles"><Icon name="card" size={16} /></button>
          <button aria-label="Ajustes"><Icon name="settings" size={16} /></button>
        </div>
        <Switch checked={on} onChange={setOn} label={`Activar ${name}`} />
      </div>
    </article>
  );
}

/* Hoja inferior con asa (transacciones sobre fondo oscuro) */
export const BottomSheet = ({ children, className }) => <section className={cx("fx-sheet-card", className)}>{children}</section>;

/* Entrada de monto con teclado numérico. Estado interno; onChange(número) en cada tecla */
export function AmountPad({ available, currency = "$", onChange, ops = true }) {
  const [v, setV] = useState("0");
  const press = (k) => {
    let next;
    if (k === "del") next = v.length > 1 ? v.slice(0, -1) : "0";
    else if (k === ".") next = v.includes(".") ? v : v + ".";
    else next = v === "0" ? k : (v.split(".")[1]?.length >= 2 ? v : v + k);
    setV(next);
    onChange?.(Number(next));
  };
  return (
    <div style={{ display: "grid", gap: 22 }}>
      <div className="fx-amount" aria-live="polite">
        <p className="fx-amount__value">{currency}{Number(v.split(".")[0]).toLocaleString()}{v.includes(".") ? "." + (v.split(".")[1] ?? "") : ""}</p>
        {available && <span className="fx-amount__hint">Available <b>{available}</b></span>}
      </div>
      {ops && <div className="fx-ops" aria-hidden="true"><span>+</span><span>−</span><span>×</span><span>÷</span></div>}
      <div className="fx-keypad">
        {["1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "0", "del"].map((k) => (
          <button key={k} onClick={() => press(k)} aria-label={k === "del" ? "Borrar" : k}>
            {k === "del" ? <Icon name="backspace" size={22} /> : k}
          </button>
        ))}
      </div>
    </div>
  );
}

/* Resumen de gasto con logos apilados (Spending $1,385 + íconos) sobre fondo oscuro */
export const SpendingPill = ({ label = "Spending", value, logos = [] }) => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, padding: "14px 16px", borderRadius: 20, background: "var(--glass-dark, rgba(255,255,255,.08))", color: "#fff", backdropFilter: "blur(10px)" }}>
    <div><div style={{ fontSize: 13, opacity: .7 }}>{label}</div><div style={{ fontSize: 18, fontWeight: 600 }}>{value}</div></div>
    <AvatarStack items={logos} max={3} />
  </div>
);

/* Tarjeta QR para vincular dispositivo */
export const QrCard = ({ qr, title, text }) => (
  <div className="fx-card fx-qr"><div className="fx-qr__frame">{qr}</div><h3 className="fx-h3" style={{ fontSize: 17 }}>{title}</h3><p className="fx-lead" style={{ fontSize: 14 }}>{text}</p></div>
);
