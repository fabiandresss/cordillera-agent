"""Convierte el informe a PDF con LibreOffice y calcula en qué página cae cada encabezado."""
import json
import subprocess
import sys
from pathlib import Path

import pymupdf

root = Path(__file__).resolve().parent.parent
docx = root / "docs" / "informe" / "Informe_EP2_ISY0101_Duoc.docx"
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
subprocess.run([r"C:\Program Files\LibreOffice\program\soffice.exe", "--headless", "--convert-to", "pdf",
                "--outdir", str(out), str(docx)], capture_output=True, timeout=240)
pdf = pymupdf.open(out / (docx.stem + ".pdf"))
marks = json.loads(docx.with_suffix(".bookmarks.json").read_text(encoding="utf-8"))
pages = {}
for name, (lvl, text) in marks.items():
    for i, page in enumerate(pdf):
        if i < 3:           # portada, ficha y contenidos
            continue
        lines = [ln.strip() for ln in page.get_text().splitlines()]
        if text in lines:
            pages[name] = i      # etiqueta de página = índice físico (la portada es 0)
            break
(out / "toc.json").write_text(json.dumps(pages), encoding="utf-8")
print("PAGINAS_TOTALES", len(pdf), "| cuerpo:", len(pdf) - 3, "| faltan:", [m for m in marks if m not in pages])
