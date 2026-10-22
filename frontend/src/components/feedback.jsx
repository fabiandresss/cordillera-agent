import { cx, Icon } from "./primitives.jsx";

/* tone: success | warning | danger | info | accent | neutral. dot = punto de color delante */
export function Badge({ tone = "neutral", dot, outline, children }) {
  return <span className={cx("fx-badge", tone !== "neutral" && `fx-badge--${tone}`, dot && "fx-badge--dot", outline && "fx-badge--outline")}>{children}</span>;
}

/* Mapea estados comunes a tonos para que todas las tablas sean coherentes */
const STATUS = { paid: "success", completed: "success", active: "success", pending: "warning", scheduled: "info", draft: "neutral", overdue: "danger", failed: "danger", canceled: "neutral" };
export const StatusBadge = ({ status }) => <Badge tone={STATUS[status.toLowerCase()] ?? "neutral"}>{status}</Badge>;

/* Variación: ↑ 12.5% from last month. dir se infiere del signo si no se pasa */
export function Delta({ value, suffix = "", dir, children }) {
  const d = dir ?? (value >= 0 ? "up" : "down");
  return (
    <span className="fx-delta" data-dir={d}>
      <Icon name={d === "up" ? "arrow-up" : "arrow-down"} size={14} stroke={2} />
      {Math.abs(value)}{suffix}
      {children && <span className="fx-delta__note">&nbsp;{children}</span>}
    </span>
  );
}

/* Barra de progreso con textos opcionales: left="50%" right="$529 / $2,000" */
export function ProgressBar({ value, max = 100, left, right, tone, size, label = "Progreso" }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className={cx("fx-progress", tone === "ink" && "fx-progress--ink", size === "lg" && "fx-progress--lg")}>
      {(left || right) && (
        <div className="fx-progress__meta"><strong>{left}</strong><span>{right}</span></div>
      )}
      <div className="fx-progress__track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={value}>
        <div className="fx-progress__fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

/* Aviso en píldora: "You have 2 credits left" + acción */
export function Notice({ icon = "info", title, text, action, onClose }) {
  return (
    <div className="fx-notice" role="status">
      <Icon name={icon} size={18} />
      <div className="fx-notice__body">
        <div className="fx-notice__title">{title}</div>
        {text && <div className="fx-notice__text">{text}</div>}
      </div>
      {action}
      {onClose && <button className="fx-iconbtn fx-iconbtn--sm" aria-label="Cerrar" onClick={onClose}><Icon name="close" size={14} /></button>}
    </div>
  );
}

export function EmptyState({ icon = "chat", title, text, action }) {
  return (
    <div className="fx-empty">
      <span className="fx-empty__icon"><Icon name={icon} size={20} /></span>
      <h3 className="fx-empty__title">{title}</h3>
      {text && <p>{text}</p>}
      {action}
    </div>
  );
}

export const Spinner = ({ label = "Cargando" }) => <span className="fx-spinner" role="status" aria-label={label} />;
