import { cx, Icon, IconButton, Avatar, Eyebrow } from "./primitives.jsx";

/* Dock flotante en píldora: el ítem activo se expande con etiqueta mono + punto.
   items: [{ id, icon, label }] */
export function Dock({ items, active, onChange }) {
  return (
    <nav className="fx-dock" aria-label="Principal">
      {items.map((it) => (
        <button key={it.id} className="fx-dock__item" aria-current={active === it.id ? "page" : undefined} aria-label={it.label} onClick={() => onChange(it.id)}>
          <Icon name={it.icon} size={18} />
          {active === it.id && <span className="fx-dock__label">{it.label}</span>}
        </button>
      ))}
    </nav>
  );
}

/* Barra negra a ancho completo, icono + texto (tema noir) */
export function TabBar({ items, active, onChange }) {
  return (
    <nav className="fx-tabbar" aria-label="Principal">
      {items.map((it) => (
        <button key={it.id} className="fx-tabbar__item" aria-current={active === it.id ? "page" : undefined} onClick={() => onChange(it.id)}>
          <Icon name={it.icon} size={22} />
          <span>{it.label}</span>
        </button>
      ))}
    </nav>
  );
}

/* Navegación superior en píldora (desktop). links: [{ id, label, href }] */
export function TopNav({ links, active }) {
  return (
    <nav className="fx-topnav" aria-label="Secciones">
      {links.map((l) => <a key={l.id} href={l.href ?? "#"} aria-current={active === l.id ? "page" : undefined}>{l.label}</a>)}
    </nav>
  );
}

/* Riel lateral de iconos circulares (desktop). items: [{ id, icon, label }] */
export function SideRail({ items, active, onChange, footer }) {
  return (
    <aside className="fx-rail" aria-label="Menú lateral">
      {items.map((it) => (
        <IconButton key={it.id} icon={it.icon} label={it.label} aria-current={active === it.id ? "page" : undefined} onClick={() => onChange?.(it.id)} />
      ))}
      {footer}
    </aside>
  );
}

/* Cabecera móvil: [grid] ........ [perfil •] [campana] */
export function AppHeader({ variant, profile = "Personal", avatarSrc, onMenu, onBell, unread }) {
  const glass = variant === "glass";
  return (
    <header className="fx-header">
      <IconButton icon="grid" label="Menú" variant={glass ? "glass" : undefined} onClick={onMenu} />
      <div style={{ display: "flex", gap: 8 }}>
        <div className={cx("fx-pillprofile", glass ? "fx-pillprofile--glass" : "fx-card--soft")} style={glass ? null : { background: "var(--surface-mute)" }}>
          <Avatar src={avatarSrc} name={profile} />
          <Eyebrow className={glass ? "" : undefined}>{profile} •</Eyebrow>
        </div>
        <IconButton icon="bell" label="Notificaciones" variant={glass ? "glass" : undefined} badge={unread} onClick={onBell} />
      </div>
    </header>
  );
}

/* Tab bar con botón central (FAB). items: 4 ítems [{id, icon, label}]; el FAB va en medio.
   activeStyle: "tint" (círculo suave, fresh) | "color" (icono en acento, ember/forest) | "block" (bloque relleno, ember perfil)
   fab: "accent" (elevado, de color) | "ink" (negro, al ras) */
export function FabTabBar({ items, active, onChange, onFab, fabIcon = "plus", fabLabel = "Crear", activeStyle = "color", fab = "accent" }) {
  const half = Math.ceil(items.length / 2);
  const render = (it) => (
    <button key={it.id} className="fx-fabbar__item" aria-current={active === it.id ? "page" : undefined} onClick={() => onChange(it.id)}>
      <span className="fx-fabbar__icon"><Icon name={it.icon} size={22} /></span>
      {it.label}
    </button>
  );
  return (
    <nav className={cx("fx-fabbar", `fx-fabbar--${activeStyle}`)} aria-label="Principal">
      {items.slice(0, half).map(render)}
      <button className={cx("fx-fab", fab === "ink" && "fx-fab--ink")} aria-label={fabLabel} onClick={onFab}><Icon name={fabIcon} size={26} /></button>
      {items.slice(half).map(render)}
    </nav>
  );
}

/* Barra flotante negra de 2–4 iconos con el activo en píldora blanca (obsidian) */
export function FloatBar({ items, active, onChange }) {
  return (
    <nav className="fx-floatbar" aria-label="Principal">
      {items.map((it) => (
        <button key={it.id} aria-label={it.label} aria-current={active === it.id ? "page" : undefined} onClick={() => onChange(it.id)}><Icon name={it.icon} size={20} /></button>
      ))}
    </nav>
  );
}

/* Sidebar vertical con etiquetas (admin, estilo FlowFin). items: [{id, icon, label, href}] */
export function Sidebar({ brand, brandIcon = "sparkle", items, active, onChange, footer }) {
  return (
    <aside className="fx-sidebar" aria-label="Menú">
      <div className="fx-sidebar__brand"><Icon name={brandIcon} size={22} />{brand}</div>
      {items.map((it) => (
        <a key={it.id} href={it.href ?? "#"} aria-current={active === it.id ? "page" : undefined} onClick={(e) => { if (onChange) { e.preventDefault(); onChange(it.id); } }}>
          <Icon name={it.icon} size={18} />{it.label}
        </a>
      ))}
      {footer && <div className="fx-sidebar__footer">{footer}</div>}
    </aside>
  );
}

/* Barra superior de admin: tabs con subrayado + búsqueda + acciones + usuario */
export function TopBar({ links = [], active, search, actions, user }) {
  return (
    <header className="fx-topbar">
      <nav className="fx-topbar__links" aria-label="Secciones">
        {links.map((l) => <a key={l.id} href={l.href ?? "#"} aria-current={active === l.id ? "page" : undefined}>{l.label}</a>)}
      </nav>
      {search}
      {actions}
      {user && (
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Avatar src={user.src} name={user.name} />
          <div style={{ lineHeight: 1.2 }}><div style={{ fontSize: 13.5, fontWeight: 600 }}>{user.name}</div><div className="fx-row__sub">{user.role}</div></div>
        </div>
      )}
    </header>
  );
}

/* Tabs con subrayado (Members / Expenses / Activity). variant="ink" usa negro en vez de acento */
export function Tabs({ tabs, value, onChange, variant }) {
  return (
    <div className={cx("fx-tabs", variant === "ink" && "fx-tabs--ink")} role="tablist">
      {tabs.map((t) => {
        const o = typeof t === "string" ? { value: t, label: t } : t;
        return <button key={o.value} role="tab" aria-selected={value === o.value} onClick={() => onChange(o.value)}>{o.label}</button>;
      })}
    </div>
  );
}

/* Chips de filtro con scroll horizontal (All / Beach / Mountains…). variant="ink" = activo negro */
export function FilterChips({ options, value, onChange, variant }) {
  return (
    <div className={cx("fx-chips", variant === "ink" && "fx-chips--ink")} role="toolbar" aria-label="Filtros">
      {options.map((o) => {
        const opt = typeof o === "string" ? { value: o, label: o } : o;
        return <button key={opt.value} aria-pressed={value === opt.value} onClick={() => onChange(opt.value)}>{opt.label}</button>;
      })}
    </div>
  );
}

/* Cabecera de página interna: [←]  Título  [acción] */
export function PageHeader({ title, onBack, action }) {
  return (
    <header className="fx-pagehead">
      {onBack ? <IconButton icon="arrow-left" label="Volver" variant="white" onClick={onBack} /> : <span />}
      <h1>{title}</h1>
      {action ?? <span />}
    </header>
  );
}

/* Fila de ajustes con chevron */
export function SettingsRow({ icon, title, sub, onClick, right }) {
  return (
    <button className="fx-setting" onClick={onClick}>
      {icon && <Icon name={icon} size={22} />}
      <span className="fx-setting__body"><span className="fx-setting__title" style={{ display: "block" }}>{title}</span>{sub && <span className="fx-setting__sub">{sub}</span>}</span>
      {right ?? <Icon name="chevron" size={18} />}
    </button>
  );
}

/* Menú de acciones con atajos (⌘N). items: [{icon, title, sub, kbd, onSelect}] */
export function ActionMenu({ label = "Actions", items }) {
  return (
    <div className="fx-menu" role="menu" aria-label={label}>
      <div className="fx-menu__label">{label}</div>
      {items.map((it) => (
        <button key={it.title} role="menuitem" onClick={it.onSelect}>
          <Icon name={it.icon} size={18} />
          <span className="fx-menu__body"><span className="fx-menu__title" style={{ display: "block" }}>{it.title}</span>{it.sub && <span className="fx-menu__sub">{it.sub}</span>}</span>
          {it.kbd && <kbd className="fx-kbd">{it.kbd}</kbd>}
        </button>
      ))}
    </div>
  );
}

export function StatusBar({ time = "9:30" }) {
  return <div className="fx-statusbar"><span>{time}</span><span aria-hidden="true">●●● ◔ ▬</span></div>;
}
