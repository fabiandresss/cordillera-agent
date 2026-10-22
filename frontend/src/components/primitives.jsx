import { useId } from "react";

export const cx = (...a) => a.filter(Boolean).join(" ");

/* ---------- Icon: set mínimo en trazo 1.6, sin dependencias ----------
   Si el proyecto ya usa lucide-react / phosphor, reemplaza este componente
   por uno que mapee los mismos nombres. */
const P = {
  home: "M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z",
  chart: "M5 20V10M12 20V4M19 20v-7",
  swap: "M4 8h14l-3-3M20 16H6l3 3",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z",
  bell: "M6 9a6 6 0 1 1 12 0c0 6 2 7 2 7H4s2-1 2-7zM10 20a2 2 0 0 0 4 0",
  grid: "M5 5h4v4H5zM15 5h4v4h-4zM5 15h4v4H5zM15 15h4v4h-4z",
  "arrow-up-right": "M7 17L17 7M8 7h9v9",
  "arrow-down-right": "M7 7l10 10M17 8v9H8",
  plus: "M12 5v14M5 12h14",
  close: "M6 6l12 12M18 6L6 18",
  eye: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21c0-4 3.6-6 8-6s8 2 8 6",
  card: "M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 10h18M7 15h3",
  wallet: "M4 7a2 2 0 0 1 2-2h11v4M4 7v10a2 2 0 0 0 2 2h13a1 1 0 0 0 1-1v-9a1 1 0 0 0-1-1H6a2 2 0 0 1-2-2zM16 14h2",
  qr: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h3v3h-3zM20 14v6M14 20h3",
  send: "M21 3L3 10l7 3 3 7z",
  history: "M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 2",
  chevron: "M9 6l6 6-6 6",
  "chevron-left": "M15 6l-6 6 6 6",
  menu: "M4 7h16M4 12h16M4 17h16",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM21 21l-5-5",
  bank: "M3 10l9-6 9 6M5 10v8M9 10v8M15 10v8M19 10v8M3 20h18",
  trend: "M3 17l6-6 4 4 8-8M15 7h6v6",
  music: "M9 18V6l10-2v12M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM19 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
  drop: "M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z",
  bolt: "M13 3L5 13h6l-1 8 8-10h-6z",
  doc: "M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6",
  logout: "M10 5H5v14h5M15 8l4 4-4 4M19 12H9",
  star: "M12 3l2.8 5.8 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.3l1.1-6.2L3 9.7l6.2-.9z",
  heart: "M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z",
  share: "M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM8.6 13.5l6.8 4M15.4 6.5l-6.8 4",
  pin: "M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21zM12 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
  plane: "M10.5 13.5L4 11l1.5-1.5 7 1 4-4a2 2 0 0 1 3 3l-4 4 1 7L16 22l-2.5-6.5-3 3V21l-1.5 1-1-3.5L4.5 17.5l1-1.5h2.5z",
  calendar: "M4 6a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zM4 10h16M8 3v4M16 3v4",
  bed: "M3 18V6M3 14h18v4M21 14v-3a3 3 0 0 0-3-3h-7v6M7 11a1.5 1.5 0 1 0 0-.01",
  utensils: "M7 3v8a2 2 0 0 0 2 2v8M5 3v5a2 2 0 0 0 2 2M9 3v5a2 2 0 0 1-2 2M17 3c-2 0-3 2-3 5s1 4 3 4v9",
  users: "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21c0-3.5 3-6 7-6s7 2.5 7 6M16 3.5a4 4 0 0 1 0 7.5M22 21c0-3-1.8-5.2-4.5-5.8",
  filter: "M4 5h16l-6 7.5V19l-4 2v-8.5z",
  more: "M5 12h.01M12 12h.01M19 12h.01",
  refresh: "M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7",
  download: "M12 4v12M7 11l5 5 5-5M5 20h14",
  chat: "M4 5h16v11H8l-4 4z",
  mail: "M3 6h18v12H3zM3 7l9 6 9-6",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
  car: "M5 16v3M19 16v3M3 16V12l2-5h14l2 5v4zM3 12h18M7 14h.01M17 14h.01",
  snow: "M12 2v20M4 6l16 12M20 6L4 18",
  backspace: "M8 5h12v14H8l-6-7zM11 9l6 6M17 9l-6 6",
  crown: "M3 8l4 4 5-7 5 7 4-4-2 11H5z",
  check: "M5 12l5 5 9-10",
  "arrow-right": "M5 12h14M13 6l6 6-6 6",
  "arrow-left": "M19 12H5M11 6l-6 6 6 6",
  "arrow-up": "M12 19V5M6 11l6-6 6 6",
  "arrow-down": "M12 5v14M6 13l6 6 6-6",
  edit: "M4 20h4L19 9l-4-4L4 16zM14 6l4 4",
  save: "M5 4h11l3 3v13H5zM8 4v5h7V4M8 20v-6h8v6",
  "file-plus": "M7 3h7l5 5v13H7zM14 3v5h5M13 12v6M10 15h6",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8h.01",
  gift: "M4 10h16v10H4zM3 7h18v3H3zM12 7v13M12 7c-1.5-3-5-3-5-1s3 1 5 1zM12 7c1.5-3 5-3 5-1s-3 1-5 1z",
  phone: "M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 4 5a1 1 0 0 1 1-1z",
  sparkle: "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z",
  compass: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM15.5 8.5l-2 5-5 2 2-5z",
  google: "M21 12.2c0-.7-.1-1.3-.2-1.9H12v3.6h5.1a4.4 4.4 0 0 1-1.9 2.9v2.4h3A9 9 0 0 0 21 12.2zM12 21c2.5 0 4.6-.8 6.2-2.3l-3-2.4c-.9.6-2 .9-3.2.9-2.4 0-4.5-1.6-5.2-3.9H3.7v2.5A9 9 0 0 0 12 21zM6.8 13.3a5.4 5.4 0 0 1 0-3.5V7.3H3.7a9 9 0 0 0 0 8.1zM12 6.6c1.3 0 2.6.5 3.5 1.4l2.7-2.7A9 9 0 0 0 3.7 7.3l3.1 2.4C7.5 7.9 9.6 6.6 12 6.6z",
};

export function Icon({ name, size = 20, stroke = 1.6, ...rest }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...rest}>
      <path d={P[name] ?? P.plus} />
    </svg>
  );
}

/* ---------- Botones ---------- */
export function Button({ variant = "primary", size, block, mono, icon, iconRight, className, children, ...rest }) {
  return (
    <button
      className={cx("fx-btn", `fx-btn--${variant}`, size && `fx-btn--${size}`, block && "fx-btn--block", mono && "fx-btn--mono", className)}
      {...rest}
    >
      {icon && <Icon name={icon} size={18} />}
      {children}
      {iconRight && <Icon name={iconRight} size={18} />}
    </button>
  );
}

export function IconButton({ icon, label, variant, size, badge, className, ...rest }) {
  return (
    <button
      aria-label={label}
      className={cx("fx-iconbtn", variant && `fx-iconbtn--${variant}`, size && `fx-iconbtn--${size}`, className)}
      {...rest}
    >
      <Icon name={icon} size={size === "sm" ? 16 : 20} />
      {badge && <span className="fx-iconbtn__badge" />}
    </button>
  );
}

/* ---------- Texto y etiquetas ---------- */
export const Eyebrow = ({ as: T = "span", className, children }) => <T className={cx("fx-eyebrow", className)}>{children}</T>;

export function Chip({ icon, variant, children }) {
  return (
    <span className={cx("fx-chip", variant && `fx-chip--${variant}`)}>
      {icon && <Icon name={icon} size={14} />}
      {children}
    </span>
  );
}

/** Titular con segunda mitad en gris: <MixedTitle strong="Make smarter decisions" muted="with real-time insights" /> */
export function MixedTitle({ as: T = "h2", strong, muted, className }) {
  return (
    <T className={cx("fx-h2 fx-title-mixed", className)}>
      {strong} {muted && <span className="fx-muted">{muted}</span>}
    </T>
  );
}

export function Avatar({ src, name = "", dark, size, className }) {
  const cls = cx("fx-avatar", dark && "fx-avatar--dark", size === "md" && "fx-avatar--md", className);
  return src ? <img className={cls} src={src} alt={name} /> : <span className={cls}>{name.slice(0, 1).toUpperCase()}</span>;
}

/* ---------- Superficies ---------- */
export function Card({ as: T = "section", soft, raised, xl, title, action, className, children, ...rest }) {
  return (
    <T className={cx("fx-card", soft && "fx-card--soft", raised && "fx-card--raised", xl && "fx-card--xl", className)} {...rest}>
      {(title || action) && (
        <header className="fx-card__head">
          <h3 className="fx-card__title">{title}</h3>
          {action}
        </header>
      )}
      {children}
    </T>
  );
}

/* ---------- Switch accesible ---------- */
export function Switch({ checked, onChange, label }) {
  const id = useId();
  return <button id={id} role="switch" aria-checked={checked} aria-label={label} className="fx-switch" onClick={() => onChange(!checked)} />;
}
