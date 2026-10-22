import { useId, useRef, useState, cloneElement, isValidElement } from "react";
import { cx, Icon, Button } from "./primitives.jsx";

/* Field: etiqueta + control + ayuda/error. Pasa el control como hijo; Field le inyecta id y aria. */
export function Field({ label, required, hint, error, children }) {
  const id = useId();
  const hintId = `${id}-hint`;
  const control = isValidElement(children)
    ? cloneElement(children, { id, "aria-invalid": !!error || undefined, "aria-describedby": hint || error ? hintId : undefined, required })
    : children;
  return (
    <div className="fx-field" data-invalid={!!error}>
      {label && <label className="fx-label" htmlFor={id}>{label}{required && <span className="fx-label__req" aria-hidden="true">*</span>}</label>}
      {control}
      {(error || hint) && <span id={hintId} className="fx-hint">{error || hint}</span>}
    </div>
  );
}

/* Input relleno (default) o blanco con sombra (variant="white"). icon = icono a la izquierda */
export function Input({ icon, variant, className, ...rest }) {
  const input = <input className={cx("fx-input", variant === "white" && "fx-input--white", className)} {...rest} />;
  return icon ? <div className="fx-input-wrap"><Icon name={icon} size={18} />{input}</div> : input;
}

export const Textarea = ({ className, ...rest }) => <textarea className={cx("fx-input", className)} {...rest} />;

/* options: string[] | {value,label}[] */
export function Select({ options = [], placeholder, className, ...rest }) {
  return (
    <select className={cx("fx-select", className)} defaultValue={rest.value === undefined ? "" : undefined} {...rest}>
      {placeholder && <option value="" disabled>{placeholder}</option>}
      {options.map((o) => {
        const opt = typeof o === "string" ? { value: o, label: o } : o;
        return <option key={opt.value} value={opt.value}>{opt.label}</option>;
      })}
    </select>
  );
}

export const Checkbox = ({ label, ...rest }) => (
  <label className="fx-choice"><input type="checkbox" className="fx-check" {...rest} />{label}</label>
);
export const Radio = ({ label, ...rest }) => (
  <label className="fx-choice"><input type="radio" className="fx-radio" {...rest} />{label}</label>
);

/* Slider con relleno de acento. Controlado: value + onChange(number) */
export function Slider({ value, min = 0, max = 100, step = 1, onChange, thin, label }) {
  const p = `${((value - min) / (max - min)) * 100}%`;
  return (
    <input type="range" aria-label={label} className={cx("fx-range", thin && "fx-range--thin")} style={{ "--p": p }}
      value={value} min={min} max={max} step={step} onChange={(e) => onChange(Number(e.target.value))} />
  );
}

/* OTP: n casillas, avanza solo, acepta pegar el código completo. group = posición del guion */
export function OtpInput({ length = 6, group = 3, onComplete }) {
  const [vals, setVals] = useState(Array(length).fill(""));
  const refs = useRef([]);
  const set = (k, v) => {
    const next = [...vals];
    v.split("").slice(0, length - k).forEach((c, j) => { next[k + j] = c; });
    setVals(next);
    const nextIdx = Math.min(k + v.length, length - 1);
    refs.current[nextIdx]?.focus();
    if (next.every(Boolean)) onComplete?.(next.join(""));
  };
  return (
    <div className="fx-otp" role="group" aria-label="Código de verificación">
      {vals.map((v, k) => (
        <span key={k} style={{ display: "contents" }}>
          {group && k === group && <span className="fx-otp__sep" aria-hidden="true">-</span>}
          <input
            ref={(el) => (refs.current[k] = el)}
            inputMode="numeric" autoComplete={k === 0 ? "one-time-code" : "off"} aria-label={`Dígito ${k + 1}`}
            value={v}
            onChange={(e) => set(k, e.target.value.replace(/\D/g, ""))}
            onKeyDown={(e) => { if (e.key === "Backspace" && !v && k) { refs.current[k - 1]?.focus(); } }}
          />
        </span>
      ))}
    </div>
  );
}

export function SearchBar({ placeholder = "Search…", value, onChange, ...rest }) {
  return (
    <label className="fx-search">
      <Icon name="search" size={18} />
      <input type="search" placeholder={placeholder} value={value} onChange={(e) => onChange?.(e.target.value)} aria-label={placeholder} {...rest} />
    </label>
  );
}

export const OrDivider = ({ children = "OR" }) => <div className="fx-or" role="separator">{children}</div>;

/* Tarjeta de registro/login: icono, título, texto, CTA, "OR", botones sociales */
export function AuthCard({ title = "Create an account", text, cta = "Get Started", onCta, providers = ["Google", "Apple"], onClose, children }) {
  return (
    <section className="fx-card fx-card--raised" style={{ display: "grid", gap: 14, textAlign: "center", position: "relative", padding: 28 }}>
      {onClose && <button className="fx-iconbtn fx-iconbtn--sm" style={{ position: "absolute", top: 14, right: 14 }} aria-label="Cerrar" onClick={onClose}><Icon name="close" size={14} /></button>}
      <span className="fx-iconbtn" style={{ margin: "0 auto" }} aria-hidden="true"><Icon name="user" size={18} /></span>
      <h2 className="fx-h3">{title}</h2>
      {text && <p className="fx-lead" style={{ margin: 0 }}>{text}</p>}
      {children}
      <Button variant="accent" block onClick={onCta}>{cta}</Button>
      {providers.length > 0 && <OrDivider />}
      {providers.map((p) => <Button key={p} variant="soft" block icon={p === "Google" ? "google" : undefined}>Continue with {p}</Button>)}
    </section>
  );
}
