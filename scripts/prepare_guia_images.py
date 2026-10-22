"""Prepara las imágenes de la guía: recortes y numeración explicativa sobre las capturas del panel."""
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "docs" / "guia" / "img"
OUT = ROOT / "docs" / "guia" / "proc"
OUT.mkdir(parents=True, exist_ok=True)

FONT_B = Path.home() / "AppData/Local/Microsoft/Windows/Fonts/Poppins-Bold.ttf"
INDIGO = (80, 70, 229)


def badge(draw, x, y, n, r=34):
    draw.ellipse((x - r, y - r, x + r, y + r), fill=INDIGO, outline=(255, 255, 255), width=5)
    f = ImageFont.truetype(str(FONT_B), 38)
    draw.text((x, y - 2), str(n), font=f, fill=(255, 255, 255), anchor="mm")


def save(im, name, q=88):
    im.convert("RGB").save(OUT / name, quality=q, optimize=True)


# --- Centro de control: dos partes, con números
dash = Image.open(IMG / "dash.png").convert("RGB")
d = ImageDraw.Draw(dash)
marks = {1: (404, 268), 2: (400, 628), 3: (1318, 628), 4: (400, 1478), 5: (400, 2146), 6: (400, 2610),
         7: (170, 560), 8: (1128, 52)}
for n, (x, y) in marks.items():
    badge(d, x, y, n)
save(dash.crop((0, 0, 2160, 1450)), "dash_a.jpg")
save(dash.crop((0, 1440, 2160, 3450)), "dash_b.jpg")

# --- otras pantallas (recortes sin espacio vacío)
for name, box in {
    "rutas": (0, 0, 2160, 1100), "pedidos": (0, 0, 2160, 1450), "memoria_corta": (0, 0, 2160, 1100),
    "memoria_larga": (0, 0, 2160, 1300), "memoria_busqueda": (0, 0, 2160, 1700),
    "asistente": (0, 0, 2160, 1000), "ajustes": (0, 0, 2160, 1000),
}.items():
    save(Image.open(IMG / f"{name}.png").crop(box), f"{name}.jpg")

# --- móvil
mv = Image.open(IMG / "movil.png").convert("RGB")
save(mv.crop((0, 0, mv.width, 2300)), "movil.jpg")

# --- robot de la plantilla (portada)
tpl = Path("C:/Users/user/Downloads/Purple Black 3D Illustration Advanced Artificial Intelligence Presentation (1).pptx")
if tpl.exists():
    with zipfile.ZipFile(tpl) as z:
        (OUT / "robot.png").write_bytes(z.read("ppt/media/image1.png"))
print("Imágenes listas en", OUT, sorted(p.name for p in OUT.iterdir()))
