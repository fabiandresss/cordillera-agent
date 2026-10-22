import { useState } from "react";
import { cx, Icon, Chip, Button, Switch, MixedTitle } from "./primitives.jsx";

/* Hero con gradiente de tema. Úsalo como cabecera de pantalla (app) o de landing (web).
   `children` va sobre el gradiente; ponle un <Sheet> debajo para el panel blanco. */
export function Hero({ bleed, className, children }) {
  return <div className={cx("fx-hero", bleed && "fx-hero--bleed", className)}>{children}</div>;
}
export const Sheet = ({ children }) => <div className="fx-sheet">{children}</div>;

/* Banner promocional. variant: "dark" | "glass" | "lime". `art` = <img> o SVG decorativo a la derecha */
export function PromoBanner({ title, art, action, variant = "dark", children }) {
  return (
    <div className={cx("fx-promo", variant !== "dark" && `fx-promo--${variant}`)}>
      <div style={{ position: "relative", zIndex: 1, display: "grid", gap: 14 }}>
        <h3 className="fx-promo__title">{title}</h3>
        {children}
        {action}
      </div>
      {art && <div className="fx-promo__art">{art}</div>}
    </div>
  );
}

/* Cabecera de sección centrada: chip + titular mixto + bajada */
export function SectionHeading({ chip, chipIcon, strong, muted, lead }) {
  return (
    <div className="fx-section">
      {chip && <Chip icon={chipIcon}>{chip}</Chip>}
      <MixedTitle strong={strong} muted={muted} />
      {lead && <p className="fx-lead">{lead}</p>}
    </div>
  );
}

/* Lista de features: la tarjeta activa se resalta con el gradiente de marca.
   items: [{ icon, title, text }] ; con `selectable` el hover/click cambia la activa */
export function FeatureList({ items, defaultActive = 0, selectable = true }) {
  const [a, setA] = useState(defaultActive);
  return (
    <div className="fx-features">
      {items.map((f, k) => (
        <article key={f.title} className={cx("fx-feature", a === k && "fx-feature--active")} onMouseEnter={() => selectable && setA(k)} onClick={() => selectable && setA(k)}>
          <span className="fx-feature__icon"><Icon name={f.icon} size={20} /></span>
          <h3 className="fx-feature__title">{f.title}</h3>
          <p className="fx-feature__text">{f.text}</p>
        </article>
      ))}
    </div>
  );
}

/* Cifras clave: 4.9 / $25M / 1600+ */
export function StatsRow({ items }) {
  return (
    <div className="fx-stats-row">
      {items.map((s) => (
        <div key={s.label}><strong>{s.value}</strong><span className="fx-eyebrow" style={{ textTransform: "none", letterSpacing: 0, fontFamily: "var(--font-sans)", fontSize: 12 }}>{s.label}</span></div>
      ))}
    </div>
  );
}

/* Testimonio con foto grande, cita, autor y selector de marcas.
   items: [{ brand, photo, quote, name, role }] */
export function Testimonials({ items }) {
  const [i, setI] = useState(0);
  const t = items[i];
  return (
    <div style={{ display: "grid", gap: 14 }}>
      <figure className="fx-quote" style={{ margin: 0 }}>
        <img className="fx-quote__photo" src={t.photo} alt={t.name} />
        <div className="fx-quote__meta" style={{ fontWeight: 600 }}>{t.brand}</div>
        <blockquote className="fx-quote__text">“{t.quote}”</blockquote>
        <figcaption className="fx-quote__meta"><strong>{t.name}</strong><div className="fx-row__sub">{t.role}</div></figcaption>
      </figure>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 4px" }}>
        <div style={{ display: "flex", gap: 14, fontSize: 11 }}>
          {items.map((x, k) => <button key={x.brand} onClick={() => setI(k)} style={{ fontWeight: k === i ? 700 : 400, color: k === i ? "var(--ink)" : "var(--ink-3)" }}>{x.brand}</button>)}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="fx-iconbtn fx-iconbtn--sm" aria-label="Anterior" onClick={() => setI((i - 1 + items.length) % items.length)}><Icon name="chevron-left" size={14} /></button>
          <button className="fx-iconbtn fx-iconbtn--sm" aria-label="Siguiente" onClick={() => setI((i + 1) % items.length)}><Icon name="chevron" size={14} /></button>
        </div>
      </div>
    </div>
  );
}

/* FAQ acordeón accesible (+ que rota a ×). items: [{ q, a }]. `single` = solo uno abierto */
export function Accordion({ items, single = false, defaultOpen = [] }) {
  const [open, setOpen] = useState(defaultOpen);
  const toggle = (k) => setOpen((o) => (o.includes(k) ? o.filter((x) => x !== k) : single ? [k] : [...o, k]));
  return (
    <div className="fx-accordion">
      {items.map((it, k) => {
        const on = open.includes(k);
        return (
          <div key={k} className="fx-acc" data-open={on}>
            <h3 style={{ margin: 0 }}>
              <button className="fx-acc__btn" aria-expanded={on} aria-controls={`acc-${k}`} onClick={() => toggle(k)}>
                {k + 1}. {it.q}
                <Icon name="plus" size={18} className="fx-acc__icon" />
              </button>
            </h3>
            <div id={`acc-${k}`} className="fx-acc__panel" role="region"><div><p>{it.a}</p></div></div>
          </div>
        );
      })}
    </div>
  );
}

/* Selector Monthly / Yearly con switch y etiqueta tipo [ GET 65% OFF ] */
export function BillingToggle({ yearly, onChange, note = "Get 65% off" }) {
  return (
    <div style={{ display: "grid", gap: 8, justifyItems: "center" }}>
      <div className="fx-toggle-row">
        <span>Monthly</span>
        <Switch checked={yearly} onChange={onChange} label="Facturación anual" />
        <span>Yearly</span>
      </div>
      <span className="fx-eyebrow">[ {note} ]</span>
    </div>
  );
}

/* Tarjeta de plan de precios. highlight = usa el gradiente de marca */
export function PricingCard({ name, tagline, price, period, features = [], cta = "Get started", highlight }) {
  return (
    <article className={cx("fx-feature", highlight && "fx-feature--active")} style={{ gap: 16 }}>
      <div>
        <h3 className="fx-feature__title">{name}</h3>
        <p className="fx-feature__text">{tagline}</p>
      </div>
      <p style={{ margin: 0, fontSize: 40, fontWeight: 600, letterSpacing: "-0.04em" }}>{price}<small style={{ fontSize: 13, opacity: 0.6, fontWeight: 400 }}> {period}</small></p>
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 8, fontSize: 14 }}>
        {features.map((f) => <li key={f} style={{ display: "flex", gap: 8 }}><Icon name="star" size={16} />{f}</li>)}
      </ul>
      <Button variant={highlight ? "accent" : "primary"} block>{cta}</Button>
    </article>
  );
}

/* Hero de landing (estilo Finexa): titular MAYÚSCULAS + bajada + CTA lima + imagen */
export function LandingHero({ title, lead, cta = "Start free trial", image, floating }) {
  return (
    <Hero bleed>
      <div style={{ display: "grid", gap: 20, padding: "24px 4px 0", maxWidth: 560 }}>
        <h1 className="fx-h1 fx-hero__title">{title}</h1>
        <p className="fx-lead" style={{ color: "var(--ink-inverse-2)" }}>{lead}</p>
        <div><Button variant="accent">{cta}</Button></div>
      </div>
      {image && <div style={{ position: "relative", marginTop: 24 }}>{image}{floating}</div>}
    </Hero>
  );
}
