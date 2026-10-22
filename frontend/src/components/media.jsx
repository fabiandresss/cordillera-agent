import { useState } from "react";
import { cx, Icon, Avatar, Button } from "./primitives.jsx";

/* Imagen con placeholder de gradiente si no hay src (nunca un hueco gris) */
export const Photo = ({ src, alt = "", className, style }) =>
  src ? <img className={cx("fx-photo", className)} src={src} alt={alt} loading="lazy" style={style} />
      : <div className={cx("fx-photo", className)} role="img" aria-label={alt} style={style} />;

export function LikeButton({ defaultOn = false, label = "Guardar en favoritos" }) {
  const [on, setOn] = useState(defaultOn);
  return (
    <button className="fx-fab-round" aria-pressed={on} aria-label={label} onClick={() => setOn(!on)}>
      <Icon name="heart" size={18} fill={on ? "currentColor" : "none"} />
    </button>
  );
}

/* Precio: "From / $799 / per person" */
export const Price = ({ from = "From", value, per = "/ per person" }) => (
  <div className="fx-price">{from && <small>{from}</small>}<strong>{value}</strong>{per && <small>{per}</small>}</div>
);

/* Tarjeta de producto/destino con foto (estilo Wanderly).
   meta: [{icon, label}] ; place: {title, sub} se muestra como píldora glass sobre la foto */
export function ImageCard({ image, alt, place, title, price, meta = [], liked, onClick }) {
  return (
    <article className="fx-imgcard" onClick={onClick}>
      <div className="fx-imgcard__media">
        <Photo src={image} alt={alt ?? title} />
        {place && (
          <div className="fx-overlay-pill">
            <Icon name="pin" size={18} />
            <div><b>{place.title}</b>{place.sub && <small>{place.sub}</small>}</div>
          </div>
        )}
        <div className="fx-overlay-btn"><LikeButton defaultOn={liked} /></div>
      </div>
      <div className="fx-imgcard__body">
        <div className="fx-imgcard__top">
          <h3 className="fx-imgcard__title">{title}</h3>
          {price && <Price value={price} />}
        </div>
        {meta.length > 0 && <div className="fx-meta">{meta.map((m) => <span key={m.label}><Icon name={m.icon} size={16} />{m.label}</span>)}</div>}
      </div>
    </article>
  );
}

/* Avatares superpuestos con "+N". items: [{src, name}] */
export function AvatarStack({ items, max = 4, size }) {
  const shown = items.slice(0, max);
  return (
    <div className="fx-avatars">
      {shown.map((a) => <Avatar key={a.name} src={a.src} name={a.name} size={size} />)}
      {items.length > max && <span className="fx-avatars__more">+{items.length - max}</span>}
    </div>
  );
}

/* Indicador de carrusel: el activo se alarga */
export const Pager = ({ total, index }) => (
  <div className="fx-pager" aria-hidden="true">{Array.from({ length: total }, (_, k) => <i key={k} data-on={k === index} />)}</div>
);

export function Gallery({ images, onViewAll, title = "Gallery" }) {
  return (
    <section style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 className="fx-display fx-display--md">{title}</h3>
        {onViewAll && <button onClick={onViewAll} style={{ fontSize: 13, display: "inline-flex", gap: 6, alignItems: "center" }}>View All <Icon name="arrow-right" size={14} /></button>}
      </div>
      <div className="fx-gallery">{images.slice(0, 3).map((src, k) => <Photo key={k} src={src} alt={`${title} ${k + 1}`} />)}</div>
    </section>
  );
}

/* Fila de beneficios con círculos pastel. items: [{icon, label, tint?}] tint = 1..4 o color CSS */
export function IconFeatures({ items }) {
  return (
    <div className="fx-icon-features">
      {items.map((f, k) => (
        <div key={f.label} className="fx-icon-feature">
          <span className="fx-icon-feature__circle" style={{ "--tint": typeof f.tint === "string" ? f.tint : `var(--tint-${f.tint ?? (k % 4) + 1})` }}>
            <Icon name={f.icon} size={22} />
          </span>
          {f.label}
        </div>
      ))}
    </div>
  );
}

/* Portada a sangre con foto: eyebrow espaciado + titular display + texto + pager.
   Debajo suele ir un <Sheet> con IconFeatures y los CTA de registro/login. */
export function CoverHero({ image, eyebrow, title, text, slides = 2, index = 0, actions, minHeight }) {
  return (
    <div className="fx-cover" style={{ minHeight }}>
      <Photo src={image} alt="" />
      {actions && <div className="fx-cover-actions">{actions}</div>}
      <div style={{ display: "grid", gap: 14, paddingBottom: 36 }}>
        {eyebrow && <span className="fx-eyebrow fx-eyebrow--wide" style={{ color: "#fff" }}>{eyebrow}</span>}
        <h1 className="fx-display fx-display--xl">{title}</h1>
        {text && <p style={{ margin: 0, maxWidth: 34 + "ch", fontSize: 14 }}>{text}</p>}
        {slides > 1 && <div style={{ color: "#fff" }}><Pager total={slides} index={index} /></div>}
      </div>
    </div>
  );
}

/* Barra inferior fija de compra: precio a la izquierda, CTA a la derecha */
export function CtaBar({ price, per = "/ per person", cta = "Book Now", onClick }) {
  return (
    <div className="fx-cta-bar">
      <div><strong style={{ fontSize: 24, letterSpacing: "-0.03em" }}>{price}</strong><div className="fx-row__sub">{per}</div></div>
      <Button variant="accent" size="lg" iconRight="arrow-right" onClick={onClick}>{cta}</Button>
    </div>
  );
}
