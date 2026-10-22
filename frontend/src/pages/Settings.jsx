import { useState } from "react";
import { Card, Segmented, Notice, SettingsRow, Badge, ActionCard, Field } from "../components";

const PROVIDERS = [
  { value: "rules", label: "Reglas" },
  { value: "ollama", label: "Ollama" },
  { value: "groq", label: "Groq" },
];
const DESC = {
  rules: "Sin LLM: clasificación por reglas y avisos por plantilla. Determinista y sin conexión.",
  ollama: "LLM local (qwen2.5:1.5b). Gratuito y privado; en CPU tarda unos 10–25 s por evento.",
  groq: "LLM en la nube (Llama 3.3 70B) con tier gratuito. Requiere GROQ_API_KEY en el archivo .env.",
};

export default function SettingsPage({ ov, onProvider, onReset, busy }) {
  const [warn, setWarn] = useState(null);
  const change = async (p) => setWarn((await onProvider(p)) ?? null);

  return (
    <>
      <div className="page-title">
        <h1 className="fx-h2" style={{ fontSize: 28 }}>Ajustes</h1>
        <p className="fx-lead" style={{ fontSize: 14 }}>Proveedor de lenguaje, jornada simulada y estado del sistema.</p>
      </div>

      <div className="fx-split" style={{ alignItems: "start" }}>
        <Card title="Modelo de lenguaje" action={<Badge tone="accent" dot>{ov.provider}</Badge>}>
          <div style={{ display: "grid", gap: 14 }}>
            <Field label="Proveedor" hint={DESC[ov.provider]}>
              <Segmented label="Proveedor de LLM" options={PROVIDERS} value={ov.provider} onChange={change} />
            </Field>
            {warn && <Notice icon="info" title="Revisa la configuración" text={warn} onClose={() => setWarn(null)} />}
            <Notice icon="shield" title="Degradación controlada"
              text="Si el LLM falla o no responde, el agente cae a reglas y plantillas, y valida toda salida del modelo contra la base de datos." />
          </div>
        </Card>

        <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
          <ActionCard title="Reiniciar jornada" sub="Regenera datos sintéticos y memoria" icon="refresh" onClick={busy ? undefined : onReset} />
          <Card title="Estado del sistema">
            <div style={{ display: "grid", gap: 4 }}>
              <SettingsRow icon="clock" title="Reloj simulado" sub={`Jornada ${ov.clock.jornada}`} right={<Badge>{ov.clock.hm}</Badge>} />
              <SettingsRow icon="history" title="Memoria corta (thread)" sub={ov.thread_id} right={<Badge>{ov.history.length} eventos</Badge>} />
              <SettingsRow icon="sparkle" title="Embeddings" sub="Memoria larga semántica"
                right={<Badge tone={ov.degraded?.length ? "warning" : "success"} dot>{ov.embeddings}</Badge>} />
              <SettingsRow icon="shield" title="Umbral de similitud" sub="Mínimo para aceptar un recuerdo" right={<Badge>0.60</Badge>} />
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
