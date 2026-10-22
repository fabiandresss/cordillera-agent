import { useRef, useState } from "react";
import { cx, Icon, Eyebrow } from "./primitives.jsx";

/* ---------- Segmented: DAY / WEEK / MONTH / YEAR ---------- */
export function Segmented({ options, value, onChange, variant = "default", label = "Rango" }) {
  return (
    <div
      role="tablist"
      aria-label={label}
      className={cx("fx-segmented", variant === "glass" && "fx-segmented--glass", variant === "plain" && "fx-segmented--plain")}
    >
      {options.map((o) => {
        const opt = typeof o === "string" ? { value: o, label: o } : o;
        return (
          <button key={opt.value} role="tab" aria-selected={value === opt.value} className="fx-segmented__item" onClick={() => onChange(opt.value)}>
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

/* ---------- Balance: "$524,381" + ".62" en gris ---------- */
export function formatMoney(n, { currency = "$", locale = "en-US" } = {}) {
  const [int, cents] = Math.abs(n).toFixed(2).split(".");
  return { sign: n < 0 ? "-" : "", currency, int: Number(int).toLocaleString(locale), cents };
}

export function Balance({ amount, size, currency, locale, showCents = true }) {
  const m = formatMoney(amount, { currency, locale });
  return (
    <p className={cx("fx-balance", size === "xl" && "fx-balance--xl")}>
      {m.sign}{m.currency}{m.int}
      {showCents && <span className="fx-balance__cents">.{m.cents}</span>}
    </p>
  );
}

/* ---------- StatCard (SPEND / SAVE / INVEST / BORROW) ---------- */
export function StatCard({ label, value, sub, icon }) {
  return (
    <div className="fx-stat">
      <div className="fx-stat__top">
        <Eyebrow>{label}</Eyebrow>
        {icon && <span className="fx-stat__icon"><Icon name={icon} size={14} /></span>}
      </div>
      <div>
        <p className="fx-stat__value">{value}</p>
        <Eyebrow>{sub}</Eyebrow>
      </div>
    </div>
  );
}

/* ---------- Gráfico de barras densas con cursor y tooltip ----------
   data: number[] ; labels?: string[] (misma longitud) para el tooltip.
   Resalta la barra bajo el puntero/teclado; sin libs de gráficos. */
export function BarChart({ data, labels = [], format = (v) => `$${v.toLocaleString()}`, startLabel, endLabel, height = 140, initial }) {
  const max = Math.max(...data, 1);
  const [i, setI] = useState(initial ?? null);
  const ref = useRef(null);

  const onMove = (e) => {
    const r = ref.current.getBoundingClientRect();
    const x = (e.touches?.[0]?.clientX ?? e.clientX) - r.left;
    setI(Math.min(data.length - 1, Math.max(0, Math.floor((x / r.width) * data.length))));
  };

  return (
    <div>
      <div
        ref={ref}
        className="fx-bars"
        style={{ height }}
        role="img"
        aria-label="Gráfico de barras"
        tabIndex={0}
        onPointerMove={onMove}
        onTouchMove={onMove}
        onKeyDown={(e) => {
          if (e.key === "ArrowRight") setI((v) => Math.min(data.length - 1, (v ?? -1) + 1));
          if (e.key === "ArrowLeft") setI((v) => Math.max(0, (v ?? 1) - 1));
        }}
      >
        {data.map((v, k) => (
          <span key={k} className="fx-bars__bar" data-on={k === i} style={{ height: `${Math.max(4, (v / max) * 100)}%` }} />
        ))}
        {i !== null && (
          <>
            <span className="fx-bars__cursor" style={{ left: `${((i + 0.5) / data.length) * 100}%` }} />
            <span className="fx-bars__tip" style={{ left: `${((i + 0.5) / data.length) * 100}%` }}>
              {format(data[i])}
              {labels[i] && <small>{labels[i]}</small>}
            </span>
          </>
        )}
      </div>
      {(startLabel || endLabel) && (
        <div className="fx-bars__axis"><Eyebrow>{startLabel}</Eyebrow><Eyebrow>{endLabel}</Eyebrow></div>
      )}
    </div>
  );
}

/* Mini barras decorativas para tarjetas de cuenta (BUSINESS / SAVINGS / TRAVEL) */
export function MiniBars({ data, highlight }) {
  const max = Math.max(...data, 1);
  return (
    <div className="fx-mini" aria-hidden="true">
      {data.map((v, k) => <span key={k} data-on={highlight?.includes(k)} style={{ height: `${Math.max(12, (v / max) * 100)}%` }} />)}
    </div>
  );
}

/* Puntos de progreso (cashback) */
export function ProgressDots({ total = 10, value = 5 }) {
  return (
    <div className="fx-dots" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={value}>
      {Array.from({ length: total }, (_, k) => <i key={k} data-on={k < value} />)}
    </div>
  );
}

/* ---------- Filas de lista: transacciones, suscripciones ---------- */
/* trailing = nodo a la izquierda del monto, en la misma fila (p. ej. flecha de entrada/salida) */
export function ListRow({ icon, avatar, title, sub, amount, side, trailing, accent, circle = false }) {
  const sign = typeof amount === "string" ? amount.trim()[0] : "";
  return (
    <li className="fx-row">
      <span className={cx("fx-row__icon", circle && "fx-row__icon--circle", accent && "fx-row__icon--accent")}>
        {avatar ?? (icon && <Icon name={icon} size={18} />)}
      </span>
      <div className="fx-row__body">
        <div className="fx-row__title">{title}</div>
        {sub && <div className="fx-row__sub">{sub}</div>}
      </div>
      {trailing}
      <div className="fx-row__side">
        {amount && <div className="fx-row__amount" data-sign={sign}>{amount}</div>}
        {side && <div className="fx-row__sub">{side}</div>}
      </div>
    </li>
  );
}

/** variant: "soft" (default, cada fila es una tarjeta gris) | "flat" (separadores) | "rounded" (blanco con borde) */
export function List({ variant = "soft", children, ...rest }) {
  return <ul className={cx("fx-list", variant !== "soft" && `fx-list--${variant}`)} {...rest}>{children}</ul>;
}

export const GroupLabel = ({ children }) => <div className="fx-group-label"><Eyebrow>{children}</Eyebrow></div>;
