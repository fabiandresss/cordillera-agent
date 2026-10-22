import { useEffect, useRef, useState } from "react";
import { Card, Notice, Button, Input, Avatar, Chip, Badge, EmptyState, Spinner } from "../components";
import { api } from "../api";

/** Render mínimo de **negritas** (el LLM las usa en sus respuestas). */
const Rich = ({ text }) => text.split(/(\*\*[^*]+\*\*)/g).map((p, i) => (p.startsWith("**") && p.endsWith("**") ? <strong key={i}>{p.slice(2, -2)}</strong> : p));

const PROMPTS = [
  "¿Qué camiones están disponibles?",
  "¿Qué pedidos quedan pendientes en la zona Sur?",
  "¿Cuál es la ruta del camión 2?",
  "¿Qué sabemos del cliente 2?",
];

export default function AssistantPage({ ov, onProvider }) {
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const end = useRef(null);
  const noLlm = ov.provider === "rules";

  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [msgs, busy]);

  const ask = async (q) => {
    const question = (q ?? text).trim();
    if (!question || busy) return;
    setText("");
    setError(null);
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setBusy(true);
    try {
      const r = await api.chat(question);
      setMsgs((m) => [...m, { role: "assistant", text: r.answer, tools: r.tools }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="page-title">
        <h1 className="fx-h2" style={{ fontSize: 28 }}>Asistente de operaciones</h1>
        <p className="fx-lead" style={{ fontSize: 14 }}>Aquí el LLM decide qué herramienta de consulta usar. Es de solo lectura: los cambios al plan pasan por el Centro de control.</p>
      </div>

      {noLlm && (
        <Notice icon="info" title="El asistente necesita un LLM"
          text="Estás en modo reglas (sin LLM). Cambia a Ollama local para conversar con el agente."
          action={<Button size="sm" variant="accent" onClick={() => onProvider("ollama")}>Usar Ollama</Button>} />
      )}

      <Card title="Conversación" action={<Badge tone="accent" dot>{ov.provider}</Badge>}>
        <div style={{ display: "grid", gap: 16 }}>
          <div className="msg-list" aria-live="polite">
            {msgs.length === 0 && (
              <EmptyState icon="chat" title="Pregunta lo que necesites" text="Consulta la flota, los pedidos, las rutas o el perfil de un cliente." />
            )}
            {msgs.map((m, i) => (
              <div key={i} className={`msg ${m.role === "user" ? "msg--user" : ""}`}>
                <Avatar name={m.role === "user" ? "Tú" : "Agente"} dark={m.role !== "user"} />
                <div>
                  <div className="msg__bubble"><Rich text={m.text} /></div>
                  {m.tools?.length > 0 && (
                    <div className="msg__tools">{[...new Set(m.tools)].map((t) => <Chip key={t} icon="bolt">{t}</Chip>)}</div>
                  )}
                </div>
              </div>
            ))}
            {busy && <div className="msg"><Avatar name="Agente" dark /><div className="msg__bubble"><Spinner label="Consultando herramientas" /></div></div>}
            <div ref={end} />
          </div>
          {error && <Notice icon="info" title="No se pudo responder" text={error} onClose={() => setError(null)} />}
          <div className="quick-row">
            {PROMPTS.map((p) => <Button key={p} type="button" variant="soft" size="sm" disabled={noLlm || busy} onClick={() => ask(p)}>{p}</Button>)}
          </div>
          <form onSubmit={(e) => { e.preventDefault(); ask(); }} style={{ display: "flex", gap: 10 }}>
            <div style={{ flex: 1 }}>
              <Input icon="chat" value={text} onChange={(e) => setText(e.target.value)} disabled={noLlm || busy}
                placeholder="Escribe tu consulta…" aria-label="Consulta al asistente" maxLength={500} />
            </div>
            <Button type="submit" icon="send" disabled={noLlm || busy || !text.trim()}>Enviar</Button>
          </form>
        </div>
      </Card>
    </>
  );
}
