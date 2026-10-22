"""Convierte la presentación a PDF con LibreOffice y genera imágenes + hoja de contactos (control visual)."""
import subprocess
import sys
from pathlib import Path

import pymupdf
from PIL import Image

root = Path(__file__).resolve().parent.parent
pptx = root / "docs" / "presentacion" / "Presentacion_EP2_Cordillera.pptx"
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
subprocess.run([r"C:\Program Files\LibreOffice\program\soffice.exe", "--headless", "--convert-to", "pdf",
                "--outdir", str(out), str(pptx)], capture_output=True, timeout=300)
pdf = pymupdf.open(out / (pptx.stem + ".pdf"))
dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 55
ims = []
for i, p in enumerate(pdf):
    f = out / f"s{i + 1:02d}.png"
    p.get_pixmap(dpi=dpi).save(f)
    ims.append(Image.open(f))
w, h = ims[0].size
cols = 3
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, h * rows), "white")
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out / "sheet.png")
print("slides", len(pdf), sheet.size)
