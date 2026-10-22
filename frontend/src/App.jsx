import { useCallback, useEffect, useState } from "react";
import { Sidebar, TopBar, Dock, IconButton, Notice, Button, Spinner, Badge, Icon } from "./components";
import { api } from "./api";
import Dashboard from "./pages/Dashboard.jsx";
import RoutesPage from "./pages/Routes.jsx";
import OrdersPage from "./pages/Orders.jsx";
import MemoryPage from "./pages/Memory.jsx";
import AssistantPage from "./pages/Assistant.jsx";
import SettingsPage from "./pages/Settings.jsx";

const NAV = [
  { id: "dash", icon: "home", label: "Centro de control" },
  { id: "routes", icon: "car", label: "Rutas y flota" },
  { id: "orders", icon: "doc", label: "Pedidos" },
  { id: "memory", icon: "history", label: "Memoria" },
  { id: "assistant", icon: "chat", label: "Asistente" },
  { id: "settings", icon: "settings", label: "Ajustes" },
];
const SHORT = { dash: "Control", routes: "Rutas", orders: "Pedidos", assistant: "Asistente", settings: "Ajustes" };
const DOCK = NAV.filter((n) => SHORT[n.id]).map((n) => ({ ...n, label: SHORT[n.id] }));
const PROVIDER_LABEL = { rules: "Modo reglas", ollama: "Ollama local", groq: "Groq" };

const PAGES = NAV.map((n) => n.id);
const fromHash = () => {
  const h = window.location.hash.replace(/^#\/?/, "").split(/[/?]/)[0];
  return PAGES.includes(h) ? h : "dash";
};

export default function App() {
  const [nav, setNavState] = useState(fromHash);
  const setNav = (id) => {
    setNavState(id);
    window.history.replaceState(null, "", `#${id}`);
  };
  useEffect(() => {
    const onHash = () => setNavState(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const [ov, setOv] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const o = await api.overview();
      setOv(o);
      setResult((r) => r ?? o.last_result);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const sendEvent = async (text) => {
    if (busy || !text?.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.event(text.trim());
      setOv(res.overview);
      setResult(res.result);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const resetDay = async () => {
    if (!window.confirm("¿Reiniciar la jornada? Se regeneran los datos sintéticos y la memoria.")) return;
    setBusy(true);
    try {
      setOv(await api.reset());
      setResult(null);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const setProvider = async (p) => {
    try {
      const res = await api.provider(p);
      setOv(res.overview);
      return res.warning;
    } catch (e) {
      setError(e.message);
      return null;
    }
  };

  if (!ov) {
    return (
      <div className="center-screen">
        {error ? (
          <div>
            <Notice icon="info" title="No se pudo conectar con el agente" text={`${error}. Verifica que la API esté en ejecución (python -m uvicorn api.main:app).`} />
            <Button icon="refresh" onClick={load}>Reintentar</Button>
          </div>
        ) : (
          <div><Spinner label="Cargando panel" /><span className="fx-muted">Iniciando agente y memoria semántica…</span></div>
        )}
      </div>
    );
  }

  const k = ov.kpis;
  const page = {
    dash: <Dashboard ov={ov} result={result} busy={busy} onEvent={sendEvent} goto={setNav} />,
    routes: <RoutesPage ov={ov} />,
    orders: <OrdersPage ov={ov} />,
    memory: <MemoryPage ov={ov} />,
    assistant: <AssistantPage ov={ov} onProvider={setProvider} />,
    settings: <SettingsPage ov={ov} onProvider={setProvider} onReset={resetDay} busy={busy} />,
  }[nav];

  return (
    <div className="app" data-theme="indigo">
      <Sidebar
        brand="Cordillera" brandIcon="car" items={NAV} active={nav} onChange={setNav}
        footer={
          <div className="fx-card fx-card--soft" style={{ display: "grid", gap: 10, padding: 16 }}>
            <strong style={{ fontSize: 14 }}>Memoria de la jornada</strong>
            <span className="fx-row__sub">{ov.history.length} eventos · {k.replans} replanificaciones</span>
            <Button variant="accent" size="sm" block icon="history" onClick={() => setNav("memory")}>Ver memoria</Button>
          </div>
        }
      />
      <div className="app__main">
        <div className="app__brand"><Icon name="car" size={22} />Cordillera</div>
        <TopBar
          search={<span className="topbar-pill"><Icon name="clock" size={16} />{ov.clock.jornada} · {ov.clock.hm}</span>}
          actions={
            <>
              <Badge tone={ov.provider === "rules" ? "neutral" : "accent"} dot>{PROVIDER_LABEL[ov.provider] ?? ov.provider}</Badge>
              <IconButton icon="refresh" label="Reiniciar jornada" variant="white" onClick={resetDay} />
              <IconButton icon="bell" label="Escalamientos al supervisor" variant="white" badge={k.escalations > 0} onClick={() => setNav("dash")} />
            </>
          }
          user={{ name: "Despachador", role: "Turno mañana" }}
        />
        <main className="app__content" id="contenido">
          {error && <Notice icon="info" title="Algo no salió como se esperaba" text={error} onClose={() => setError(null)} />}
          {ov.degraded?.length > 0 && (
            <Notice icon="info" title="Modo degradado" text="Ollama no responde: la memoria semántica usa embeddings simplificados. Inicia Ollama y reinicia el servidor para recuperar la búsqueda completa." />
          )}
          {page}
        </main>
        <div className="app__dock"><Dock items={DOCK} active={nav} onChange={setNav} /></div>
      </div>
    </div>
  );
}
