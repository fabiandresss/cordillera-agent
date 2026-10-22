"""Ejecuta los escenarios de demo y guarda el razonamiento del agente en docs/evidencia/.

Uso:
    python scripts/generate_evidence.py                  # reglas + embeddings reales (Ollama)
    python scripts/generate_evidence.py --llm ollama     # LLM local qwen2.5:1.5b (más lento)
    python scripts/generate_evidence.py --llm groq       # requiere GROQ_API_KEY en .env
"""
import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ap = argparse.ArgumentParser()
ap.add_argument("--llm", default="rules", choices=["rules", "ollama", "groq"])
ap.add_argument("--embeddings", default="ollama", choices=["ollama", "fake"])
ap.add_argument("--out", default=str(ROOT / "docs" / "evidencia"))
args = ap.parse_args()

os.environ["LLM_PROVIDER"] = args.llm
os.environ["EMBEDDINGS_PROVIDER"] = args.embeddings
if args.embeddings == "fake":
    os.environ["SIMILARITY_THRESHOLD"] = "0.25"

work = Path(tempfile.mkdtemp(prefix="cordillera_evidence_"))
base = work / "base"
os.environ["CORDILLERA_STATE_DIR"] = str(base)
os.environ["CORDILLERA_OUTPUT_DIR"] = str(work / "out_base")

from src import config, db, memory  # noqa: E402
from src.agent import DispatchAgent  # noqa: E402
from tests.scenarios import scenarios  # noqa: E402

spec = importlib.util.spec_from_file_location("seed", ROOT / "data" / "seed.py")
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)
seed.build()
memory.index_all()

out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)
rows = []

for name, fn in scenarios.ALL:
    state_dir = work / name
    shutil.copytree(base, state_dir)
    os.environ["CORDILLERA_STATE_DIR"] = str(state_dir)
    os.environ["CORDILLERA_OUTPUT_DIR"] = str(work / f"{name}_out")
    if name == "escenario_6_llm_caido":  # simula proveedor sin clave/caído
        os.environ["LLM_PROVIDER"], os.environ["GROQ_API_KEY"] = "groq", ""
    else:
        os.environ["LLM_PROVIDER"] = args.llm
    agent = DispatchAgent(thread_id=f"evidencia-{name}", index=False)
    results, summary = fn(agent)

    md = [f"# {name.replace('_', ' ').capitalize()}", "",
          f"_Proveedor LLM: `{args.llm}` · embeddings: `{args.embeddings}` · "
          f"umbral de similitud: {config.similarity_threshold()}_", ""]
    for i, (event, st) in enumerate(results, 1):
        md += [f"## Evento {i}: «{event}»", "", "```text"]
        md += [line.replace("**", "") for line in st["log"]]
        md += ["```", "", f"**Resultado:** `{st['outcome']}`"]
        if st.get("needs_info"):
            md.append(f" · pregunta al usuario: {st['needs_info']}")
        if st["notifications"]:
            md += ["", "Ejemplos de avisos a clientes:"]
            md += [f"- (cliente {n['client_id']}, pedido {n['order_id']}, {n['kind']}) {n['message']}"
                   for n in st["notifications"][:3]]
        md.append("")
    md += ["## Resumen verificable", "", "```json", json.dumps(summary, ensure_ascii=False, indent=2, default=str), "```", ""]
    (out_dir / f"{name}.md").write_text("\n".join(md), encoding="utf-8")
    rows.append((name, summary))
    print(f"OK {name}: {summary}")

(out_dir / "README.md").write_text(
    "# Evidencia de pruebas de escenarios\n\n"
    f"Generado con `python scripts/generate_evidence.py --llm {args.llm} --embeddings {args.embeddings}`.\n\n"
    "Cada archivo muestra el razonamiento paso a paso del agente (nodo por nodo) y un resumen "
    "verificable del estado final. Las mismas condiciones se verifican automáticamente en "
    "`tests/test_scenarios.py`.\n\n"
    + "\n".join(f"- [{n}]({n}.md)" for n, _ in rows) + "\n", encoding="utf-8")
shutil.rmtree(work, ignore_errors=True)
