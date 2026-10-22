"""Genera los diagramas PNG de docs/ (arquitectura, flujo del grafo y boceto de la UI).

Uso:  python scripts/make_diagrams.py   (requiere matplotlib)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIAG = ROOT / "docs" / "diagramas"
BOC = ROOT / "docs" / "bocetos"
DIAG.mkdir(parents=True, exist_ok=True)
BOC.mkdir(parents=True, exist_ok=True)

C = {"ui": "#dbeafe", "agent": "#e0e7ff", "node": "#ede9fe", "tool": "#dcfce7",
     "store": "#fef9c3", "llm": "#fee2e2", "end": "#e5e7eb", "warn": "#ffedd5"}


def box(ax, x, y, w, h, text, color, fs=9, bold=False, ec="#374151"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=color, ec=ec, lw=1.2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
            wrap=True)


def arrow(ax, p1, p2, label="", rad=0.0, color="#374151", ls="-", fs=8, lx=0, ly=0):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=12, lw=1.3, color=color,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p1[0] + p2[0]) / 2 + lx, (p1[1] + p2[1]) / 2 + ly, label, fontsize=fs, ha="center",
                va="center", color=color, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w / 10, h / 10), dpi=170)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=8)
    return fig, ax


# ---------------------------------------------------------------- 1. arquitectura
fig, ax = canvas(160, 100, "Arquitectura de componentes · Agente de despacho Transportes Cordillera")
box(ax, 18, 92, 26, 7, "Despachador\n(eventos en lenguaje natural)", C["ui"])
box(ax, 62, 92, 34, 7, "Streamlit UI  (src/app.py)\nOperación · Consultas · Memoria", C["ui"])
box(ax, 118, 92, 38, 7, "DispatchAgent  (src/agent.py)\nthread_id = jornada", C["agent"], bold=True)
arrow(ax, (28.5, 92), (39.5, 92))
arrow(ax, (84.5, 92), (98, 92))

ax.add_patch(FancyBboxPatch((6, 38), 148, 40, boxstyle="round,pad=0.5,rounding_size=2", fc="#faf5ff",
                            ec="#7c3aed", lw=1.8, ls="--"))
ax.text(10, 75, "Grafo LangGraph (src/graph.py): orquestación con decisiones condicionales", fontsize=10,
        fontweight="bold", color="#6d28d9", va="center")
nodes = [("ingest +\nclassify", 20), ("retrieve_\ncontext", 42), ("apply_\nevent", 64), ("plan", 84),
         ("validate ⇄\nrepair", 104), ("execute", 124), ("draft +\nnotify_log", 143)]
for t, x in nodes:
    box(ax, x, 56, 16, 9, t, C["node"], fs=8.5)
for (_, a), (_, b) in zip(nodes, nodes[1:]):
    arrow(ax, (a + 8.4, 56), (b - 8.4, 56))
box(ax, 42, 43.5, 30, 5, "escalate · clarify · record_only (salidas alternativas)", C["warn"], fs=7.5)
box(ax, 118, 43.5, 44, 5, "Planificador determinista (src/planner.py): prioridad, asignación, ETA, reparación", C["tool"], fs=7.5)
arrow(ax, (118, 46), (104, 51.5), ls=":")
arrow(ax, (118, 46), (84, 51.5), ls=":")
arrow(ax, (118, 92 - 3.7), (118, 78.5))

box(ax, 28, 21, 40, 13, "Herramientas de CONSULTA\nget_fleet_status · get_pending_orders\nget_traffic · get_client_profile · get_route\nsearch_past_incidents · search_policies", C["tool"], fs=8)
box(ax, 76, 21, 40, 13, "Herramientas de ESCRITURA\nassign_orders · write_route_sheet\nnotify_client · notify_supervisor\nreschedule_order · log_incident", C["tool"], fs=8)
box(ax, 124, 21, 40, 13, "Herramienta de RAZONAMIENTO\nclassify_event (LLM + reglas)\nredacción de avisos (LLM + plantillas)\nguardarraíles anti-alucinación", C["llm"], fs=8)
for x in (28, 76, 124):
    arrow(ax, (x, 38), (x, 27.8))

box(ax, 22, 5, 30, 7, "SQLite  (cordillera.db)\nflota · pedidos · clientes · incidentes", C["store"], fs=7.5)
box(ax, 58, 5, 30, 7, "ChromaDB (memoria larga)\nincidentes + políticas, coseno", C["store"], fs=7.5)
box(ax, 94, 5, 30, 7, "Checkpointer SQLite\n(memoria corta por thread_id)", C["store"], fs=7.5)
box(ax, 134, 5, 38, 7, "LLM: Groq (nube gratuita) | Ollama (local)\n| rules (sin LLM)  ·  Embeddings: nomic-embed-text", C["llm"], fs=7)
arrow(ax, (22, 8.6), (28, 14.5))
arrow(ax, (76, 14.5), (30, 8.6), rad=0.15)
arrow(ax, (58, 8.6), (36, 14.5))
arrow(ax, (134, 8.6), (124, 14.5))
arrow(ax, (94, 8.6), (110, 38), rad=-0.25, ls="--")
fig.tight_layout()
fig.savefig(DIAG / "arquitectura.png")
plt.close(fig)

# ---------------------------------------------------------------- 2. flujo del grafo
fig, ax = canvas(170, 80, "Flujo del grafo LangGraph y aristas condicionales")
Y = 48
xs = {"ingest_event": 9, "classify_event": 28, "retrieve_context": 49, "apply_event": 69, "plan": 87,
      "validate": 105, "execute": 123, "draft_notifications": 142, "notify_and_log": 160}
for n, x in xs.items():
    box(ax, x, Y, 15.5, 8, n.replace("_", "_\n", 1) if len(n) > 12 else n, C["node"], fs=7.5)
order = list(xs)
for a_, b_ in zip(order, order[1:]):
    if (a_, b_) == ("validate", "execute"):
        arrow(ax, (xs[a_] + 8.2, Y), (xs[b_] - 8.2, Y), "ok", ly=3.2, fs=7.5, color="#15803d")
    else:
        arrow(ax, (xs[a_] + 8.2, Y), (xs[b_] - 8.2, Y))
box(ax, 20, 22, 18, 8, "escalate\n(evento no reconocido)\n→ FIN", C["warn"], fs=7)
box(ax, 42, 22, 18, 8, "clarify\n(falta camión/pedido)\n→ FIN", C["warn"], fs=7)
box(ax, 69, 22, 18, 8, "record_only\n(sin acción)\n→ FIN", C["warn"], fs=7)
box(ax, 105, 72, 15.5, 8, "repair", C["node"], fs=8)
box(ax, 120, 22, 22, 8, "escalate_partial\n(ventanas imposibles)", C["warn"], fs=7)
arrow(ax, (26, Y - 4.4), (21, 26.5), "tipo = otro", fs=7, lx=-5)
arrow(ax, (31, Y - 4.4), (40, 26.5), "falta dato", fs=7, lx=6)
arrow(ax, (69, Y - 4.4), (69, 26.5), "sin acción", fs=7, lx=6)
arrow(ax, (101, Y + 4.4), (101, 67.6), "viola y\nrepair < 3", fs=7, lx=-8, color="#b45309")
arrow(ax, (109, 67.6), (109, Y + 4.4), "", color="#b45309")
arrow(ax, (107, Y - 4.4), (114, 26.5), "reparaciones\nagotadas", fs=7, lx=-8, color="#b91c1c")
arrow(ax, (124, 26.5), (124, Y - 4.4), "", color="#b91c1c")
ax.text(5, 8, "Notas: apply_event pasa directo a draft_notifications cuando no hace falta replanificar "
              "(reprogramar para mañana o escalar un pedido).\n"
              "notify_and_log termina el flujo. Todo el estado viaja en AgentState; el checkpointer lo "
              "persiste por thread_id (memoria corta).", fontsize=8, color="#374151", va="center")
fig.tight_layout()
fig.savefig(DIAG / "flujo_grafo.png")
plt.close(fig)

# ---------------------------------------------------------------- 3. boceto de UI
fig, ax = canvas(130, 86, "Boceto del panel web (wireframe) · frontend/ · tema indigo del kit fintech-ui-react")
ax.add_patch(FancyBboxPatch((1.5, 2), 127, 78, boxstyle="round,pad=0.3", fc="white", ec="#111827", lw=1.5))
# sidebar
box(ax, 13, 41, 20, 70, "", "#f3f4f6")
ax.text(13, 74, "Cordillera", ha="center", fontweight="bold", fontsize=9)
for i, t in enumerate(["Centro de control", "Rutas y flota", "Pedidos", "Memoria", "Asistente", "Ajustes"]):
    box(ax, 13, 67 - i * 6.2, 16, 4, t, "#5046e5" if i == 0 else "white", fs=7)
    if i == 0:
        ax.texts[-1].set_color("white")
box(ax, 13, 12, 16, 8, "Memoria de la jornada\n[Ver memoria]", "white", fs=6.5)
# topbar
box(ax, 75, 76, 80, 4.2, "reloj simulado · proveedor LLM · reiniciar · avisos · usuario", "#eef0f8", fs=7)
# kpis
kp = [("Entregas pendientes", "#5046e5"), ("Camiones operativos", "white"), ("Replanificaciones", "white"), ("Avisos a clientes", "white")]
for i, (t, col) in enumerate(kp):
    box(ax, 42 + i * 21.5, 67, 19, 9, t + "\n(KpiCard)", col, fs=6.5)
    if col != "white":
        ax.texts[-1].set_color("white")
# console + reasoning
box(ax, 54, 49, 40, 17, "Consola de eventos\nCampo de texto + [Enviar al agente]\nEscenarios rápidos (chips)\nResultado (Notice)", "white", fs=7)
box(ax, 100, 49, 36, 17, "Razonamiento del agente\nlínea de tiempo paso a paso\n(ListRow con iconos)", "white", fs=7)
# fleet table
box(ax, 75, 33, 80, 11, "Flota (DataTable oscuro): camión · estado · carga · paradas · zona", "#1b1c3d", fs=7.5)
ax.texts[-1].set_color("white")
# charts
box(ax, 54, 17, 40, 14, "Carga por camión\n(ColumnChart)", "white", fs=7)
box(ax, 100, 17, 36, 14, "Estado de pedidos\n(DonutChart)", "white", fs=7)
ax.text(75, 4.2, "Móvil (< 900 px): una columna y Dock inferior en lugar del sidebar", ha="center", fontsize=7.5, color="#374151")
fig.tight_layout()
fig.savefig(BOC / "boceto_ui.png")
plt.close(fig)
print("Diagramas generados en", DIAG, "y", BOC)


# ---------------------------------------------------------------- 4. diagramas simples (informe y presentación)
# Lienzo angosto (7,2 in) para que la tipografía se lea bien al insertarlos en una página A4.
def simple_canvas(w_in, h_in):
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=260)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h_in / w_in)
    ax.axis("off")
    return fig, ax


def sbox(ax, x, y, w, h, text, color, fs=10.5, bold=False, ec="#374151", tc="#111827"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.4,rounding_size=2",
                                fc=color, ec=ec, lw=1.4))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
            color=tc, linespacing=1.2)


def sarrow(ax, p1, p2, label="", color="#374151", rad=0.0, fs=9, lx=0, ly=0):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13, lw=1.5, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p1[0] + p2[0]) / 2 + lx, (p1[1] + p2[1]) / 2 + ly, label, fontsize=fs, ha="center",
                va="center", color=color, bbox=dict(fc="white", ec="none", pad=0.8))


# --- arquitectura simple
fig, ax = simple_canvas(7.2, 5.0)
sbox(ax, 15, 61, 26, 9.5, "Despachador", C["ui"], 11, True)
sbox(ax, 50, 61, 26, 9.5, "Panel web", C["ui"], 11, True)
sbox(ax, 85, 61, 26, 9.5, "API", C["ui"], 11, True)
sarrow(ax, (28.4, 61), (36.6, 61))
sarrow(ax, (63.4, 61), (71.6, 61))
ax.add_patch(FancyBboxPatch((3, 22), 94, 30, boxstyle="round,pad=0.4,rounding_size=2", fc="#faf5ff", ec="#7c3aed", lw=1.8, ls="--"))
ax.text(50, 48.4, "Agente (LangGraph)", ha="center", va="center", fontsize=11, fontweight="bold", color="#6d28d9")
for i, t in enumerate(["Entiende\nel mensaje", "Recuerda\ncasos", "Planifica\ny revisa", "Actúa\ny avisa"]):
    x = 16.5 + i * 22.3
    sbox(ax, x, 33, 18.5, 11.5, t, C["node"], 10)
    if i:
        sarrow(ax, (x - 22.3 + 9.7, 33), (x - 9.7, 33))
sarrow(ax, (85, 56.2), (85, 52.6))
sbox(ax, 17, 8, 29, 11, "Herramientas\n(consultar y escribir)", C["tool"], 10)
sbox(ax, 50, 8, 29, 11, "Memoria\n(corta y larga)", C["store"], 10)
sbox(ax, 83, 8, 29, 11, "IA de lenguaje\n(Groq, Ollama, reglas)", C["llm"], 10)
for x in (17, 50, 83):
    sarrow(ax, (x, 21.2), (x, 14.2), color="#6b7280")
fig.savefig(DIAG / "arquitectura_simple.png", bbox_inches="tight", pad_inches=0.06)
plt.close(fig)

# --- flujo simple
fig, ax = simple_canvas(7.2, 3.5)
xs = [7.6, 21.8, 36.0, 50.2, 64.4, 78.6, 92.8]
labels = ["Mensaje\nrecibido", "Entender\nel mensaje", "Recordar\ncasos", "Decidir\nqué hacer",
          "Planificar\nentregas", "Revisar\nel plan", "Ejecutar\ny avisar"]
for x, t in zip(xs, labels):
    sbox(ax, x, 38, 12.6, 11, t, C["node"], 8.6)
for a_, b_ in zip(xs, xs[1:]):
    sarrow(ax, (a_ + 6.9, 38), (b_ - 6.9, 38))
sbox(ax, 14, 8.5, 20, 10, "Pedir el dato\nque falta", C["warn"], 9)
sbox(ax, 41, 8.5, 20, 10, "Avisar al\nsupervisor", C["warn"], 9)
sbox(ax, 79, 8.5, 25, 10, "Corregir el plan\n(hasta 3 veces)", C["warn"], 9)
sarrow(ax, (19.5, 32.2), (14.5, 13.8), "falta un dato", "#b45309", lx=-8, fs=8.2)
sarrow(ax, (25, 32.2), (38, 13.8), "no se entiende", "#b91c1c", lx=10, ly=1, fs=8.2)
sarrow(ax, (78.6, 32.2), (78.8, 13.8), "no cumple", "#b45309", lx=7.5, fs=8.2)
sarrow(ax, (72, 13.8), (64.4, 32.2), "reintenta", "#b45309", rad=-0.12, lx=-7, fs=8.2)
sarrow(ax, (66.2, 8.5), (51.3, 8.5), "sigue fallando", "#b91c1c", ly=3.4, fs=8.2)
fig.savefig(DIAG / "flujo_simple.png", bbox_inches="tight", pad_inches=0.06)
plt.close(fig)
print("Diagramas simples generados")
