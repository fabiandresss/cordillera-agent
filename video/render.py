"""Editor de video programático: escenas animadas + capturas reales + voz + sonido  ->  MP4.

Uso:
    python video/render.py stills      # imágenes de control en video/stills/
    python video/render.py full        # video completo en video/out/
"""
import json
import math
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sound  # noqa: E402

W, H, FPS = 1920, 1080, 30
TARGET = 120.0          # duración objetivo del video (s)
OVERLAP = 0.6           # duración de cada transición (s)

BLACK, YEL, GRAY = (27, 27, 27), (229, 174, 56), (107, 107, 107)
LINE, SOFT, WHITE = (220, 220, 220), (245, 245, 245), (255, 255, 255)
INDIGO, RED, GREEN = (80, 70, 229), (214, 69, 69), (46, 158, 91)
YEL_SOFT, INDIGO_SOFT = (251, 240, 214), (236, 234, 253)

FONTS = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
UIFONT = Path("C:/Windows/Fonts/segoeui.ttf")


# ------------------------------------------------------------------ utilidades
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def eo(x):          # ease-out cúbico
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eio(x):         # ease-in-out suave
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eob(x):         # ease-out con rebote (back)
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


_fonts = {}


def F(sz, bold=False, ui=False):
    key = (sz, bold, ui)
    if key not in _fonts:
        path = UIFONT if ui else FONTS / ("Poppins-Bold.ttf" if bold else "Poppins-Regular.ttf")
        _fonts[key] = ImageFont.truetype(str(path), sz)
    return _fonts[key]


_sp = {}


def tsp(text, sz, color=BLACK, bold=False, ui=False):
    """Sprite RGBA de texto (en caché)."""
    key = (text, sz, color, bold, ui)
    if key not in _sp:
        f = F(sz, bold, ui)
        l, t, r, b = f.getbbox(text)
        im = Image.new("RGBA", (r + 10, int(sz * 1.55)), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4, 0), text, font=f, fill=color + (255,))
        _sp[key] = im
    return _sp[key]


def put(fr, sp, x, y, a=1.0, s=1.0, center=False):
    if a <= 0.003:
        return
    if s != 1.0:
        sp = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)
    if center:
        x, y = x - sp.width / 2, y - sp.height / 2
    if a < 1.0:
        al = sp.getchannel("A").point(lambda v: int(v * a))
        sp = sp.copy()
        sp.putalpha(al)
    fr.paste(sp, (int(x), int(y)), sp)


_cards = {}


def card_sp(w, h, r=34, fill=WHITE, line=LINE, shadow=True, lw=2):
    key = (w, h, r, fill, line, shadow, lw)
    if key not in _cards:
        pad = 46
        im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        if shadow:
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 12, pad + w, pad + h + 12), r, fill=(25, 25, 50, 58))
            im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(16)))
        big = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0))
        ImageDraw.Draw(big).rounded_rectangle((0, 0, w * 3 - 1, h * 3 - 1), r * 3, fill=fill + (255,),
                                               outline=(line + (255,)) if line else None, width=lw * 3)
        im.alpha_composite(big.resize((w, h), Image.LANCZOS), (pad, pad))
        _cards[key] = (im, pad)
    return _cards[key]


def card(fr, x, y, w, h, a=1.0, s=1.0, **kw):
    sp, pad = card_sp(w, h, **kw)
    cx, cy = x + w / 2, y + h / 2
    put(fr, sp, cx, cy, a, s, center=True)


def pill(fr, x, y, label, sz=30, fill=YEL, color=BLACK, a=1.0, s=1.0, bold=True, padx=34, h=None):
    t = tsp(label, sz, color, bold)
    w = t.width + 2 * padx - 8
    h = h or int(sz * 2.1)
    card(fr, x, y, w, h, a, s, r=h // 2, fill=fill, line=None, shadow=False)
    cx, cy = x + w / 2, y + h / 2
    put(fr, t, cx, cy - 2, a, s, center=True)
    return w


def icon_sp(kind, size=150, bg=BLACK):
    key = ("icon", kind, size, bg)
    if key in _sp:
        return _sp[key]
    S4 = 4
    im = Image.new("RGBA", (size * S4, size * S4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size * S4
    d.rounded_rectangle((0, 0, s - 1, s - 1), int(s * 0.22), fill=bg + (255,))
    u = s / 150.0
    wcol = (255, 255, 255, 255)
    if kind == "truck":
        d.rounded_rectangle((26 * u, 48 * u, 88 * u, 96 * u), 6 * u, fill=wcol)
        d.polygon([(92 * u, 62 * u), (116 * u, 62 * u), (128 * u, 80 * u), (128 * u, 96 * u), (92 * u, 96 * u)], fill=wcol)
        for cx in (50 * u, 108 * u):
            d.ellipse((cx - 12 * u, 90 * u, cx + 12 * u, 114 * u), fill=wcol, outline=bg + (255,), width=int(5 * u))
            d.ellipse((cx - 4 * u, 98 * u, cx + 4 * u, 106 * u), fill=bg + (255,))
    elif kind == "crown":
        d.polygon([(32 * u, 104 * u), (26 * u, 54 * u), (52 * u, 78 * u), (75 * u, 40 * u), (98 * u, 78 * u), (124 * u, 54 * u),
                   (118 * u, 104 * u)], fill=wcol)
        d.rounded_rectangle((32 * u, 108 * u, 118 * u, 118 * u), 4 * u, fill=(229, 174, 56, 255))
    elif kind == "box":
        d.rounded_rectangle((34 * u, 42 * u, 116 * u, 112 * u), 8 * u, outline=wcol, width=int(8 * u))
        d.line((48 * u, 58 * u, 102 * u, 96 * u), fill=(229, 174, 56, 255), width=int(10 * u))
        d.line((102 * u, 58 * u, 48 * u, 96 * u), fill=(229, 174, 56, 255), width=int(10 * u))
    elif kind == "brain":     # IA: destellos
        for cx, cy, r in ((75, 75, 26), (112, 44, 12), (40, 108, 10)):
            d.polygon([(cx * u, (cy - r) * u), ((cx + r * .3) * u, (cy - r * .3) * u), ((cx + r) * u, cy * u), ((cx + r * .3) * u, (cy + r * .3) * u),
                       (cx * u, (cy + r) * u), ((cx - r * .3) * u, (cy + r * .3) * u), ((cx - r) * u, cy * u), ((cx - r * .3) * u, (cy - r * .3) * u)], fill=wcol)
    elif kind == "check":
        d.line((40 * u, 80 * u, 66 * u, 106 * u), fill=wcol, width=int(14 * u))
        d.line((66 * u, 106 * u, 112 * u, 48 * u), fill=wcol, width=int(14 * u))
    elif kind == "book":
        d.rounded_rectangle((38 * u, 36 * u, 112 * u, 114 * u), 8 * u, fill=wcol)
        for yy in (58, 78, 98):
            d.line((52 * u, yy * u, 98 * u, yy * u), fill=bg + (255,), width=int(5 * u))
    elif kind == "archive":
        d.rounded_rectangle((30 * u, 40 * u, 120 * u, 62 * u), 5 * u, fill=wcol)
        d.rounded_rectangle((38 * u, 66 * u, 112 * u, 116 * u), 5 * u, fill=wcol)
        d.rounded_rectangle((60 * u, 78 * u, 90 * u, 88 * u), 4 * u, fill=bg + (255,))
    elif kind == "gear":
        d.ellipse((46 * u, 46 * u, 104 * u, 104 * u), fill=wcol)
        for k in range(8):
            a = k * math.pi / 4
            d.ellipse(((75 + 38 * math.cos(a) - 9) * u, (75 + 38 * math.sin(a) - 9) * u,
                       (75 + 38 * math.cos(a) + 9) * u, (75 + 38 * math.sin(a) + 9) * u), fill=wcol)
        d.ellipse((62 * u, 62 * u, 88 * u, 88 * u), fill=bg + (255,))
    out = im.resize((size, size), Image.LANCZOS)
    _sp[key] = out
    return out


def pointer_sp():
    if "ptr" not in _sp:
        S = 4
        im = Image.new("RGBA", (30 * S, 42 * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = [(2, 2), (2, 30), (9, 24), (14, 36), (19, 34), (14, 22), (24, 22)]
        d.polygon([(x * S, y * S) for x, y in pts], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=2 * S)
        _sp["ptr"] = im.resize((30, 42), Image.LANCZOS)
    return _sp["ptr"]


# ------------------------------------------------------------------ recursos
def load_asset(name):
    return Image.open(HERE / "assets" / name).convert("RGBA")


LOGO = load_asset("logo.png")
ROBOT1 = load_asset("robot1.png")
ROBOT2 = load_asset("robot2.png")
SHOTS = {k: Image.open(HERE / "shots" / f"{k}.png").convert("RGB")
         for k in ("A_limpio", "C_averia_top", "C_averia_full", "D_busqueda", "E_rutas")}

_base = {}


def base(tag):
    """Fondo blanco con etiqueta y logo, igual que la plantilla del PPT."""
    if tag not in _base:
        im = Image.new("RGB", (W, H), WHITE)
        d = ImageDraw.Draw(im)
        d.ellipse((96, 66, 126, 96), fill=BLACK)
        put(im, tsp(tag, 26, BLACK), 142, 58)
        lg = LOGO.resize((190, int(190 * LOGO.height / LOGO.width)), Image.LANCZOS)
        im.paste(lg, (W - 96 - lg.width, 60), lg)
        _base[tag] = im
    return _base[tag].copy()


def title(fr, text, t, t0=0.0, y=165, sz=74):
    a = eo((t - t0) / 0.6)
    sp = tsp(text, sz, BLACK, True)
    put(fr, sp, W / 2, y + (1 - a) * 28, a, center=True)


# ------------------------------------------------------------------ audio / cues
class Narr:
    def __init__(self, i, lead, tail):
        j = json.loads((HERE / "audio" / f"s{i:02d}.json").read_text(encoding="utf-8"))
        self.i, self.lead, self.tail, self.voice = i, lead, tail, j["duration"]
        self.words = [(re.sub(r"[^a-záéíóúñü0-9]", "", w["w"].lower()), w["t"] + lead, w["d"]) for w in j["words"]]
        self.dur = lead + self.voice + tail

    def cue(self, key, n=0, default=None, end=False):
        hits = [(t, d) for w, t, d in self.words if w.startswith(key)]
        if len(hits) > n:
            t, d = hits[n]
            return t + (d if end else 0)
        if default is None:
            raise KeyError(f"escena {self.i}: no hay palabra «{key}»")
        return default


LEADS_TAILS = {1: (1.6, 1.3), 2: (0.7, 1.2), 3: (1.0, 1.9), 4: (0.7, 1.4), 5: (0.7, 1.5), 6: (0.7, 1.4), 7: (0.7, 1.6), 8: (0.7, 4.0)}
N = {i: Narr(i, *LEADS_TAILS[i]) for i in range(1, 9)}
EVENTS = {}      # (escena, t_local, nombre) -> (ganancia, pan)


def ev(i, t, name, g=1.0, pan=0.0):
    EVENTS[(i, round(t, 3), name)] = (g, pan)


# ------------------------------------------------------------------ cámara sobre capturas reales
CSS_W = 1920


def shot_frame(fr, shot, cx, cy, cw, fx=96, fy=60, fw=1728, fh=950, radius=30):
    """Dibuja una región de la captura dentro de un marco con sombra. Devuelve (x0, y0, cw, ch) en px CSS."""
    img = SHOTS[shot]
    css_h = img.height / 2
    ch = cw * fh / fw
    x0 = clamp(cx - cw / 2, 0, CSS_W - cw)
    y0 = clamp(cy - ch / 2, 0, css_h - ch)
    reg = img.resize((fw, fh), Image.BILINEAR, box=(x0 * 2, y0 * 2, (x0 + cw) * 2, (y0 + ch) * 2))
    mask = Image.new("L", (fw * 2, fh * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw * 2 - 1, fh * 2 - 1), radius * 2, fill=255)
    mask = mask.resize((fw, fh), Image.LANCZOS)
    sp, pad = card_sp(fw, fh, r=radius, fill=WHITE, line=LINE, shadow=True)
    fr.paste(sp, (fx - pad, fy - pad), sp)
    fr.paste(reg, (fx, fy), mask)
    return x0, y0, cw, ch, fx, fy, fw, fh


def m2o(cam, x, y):
    x0, y0, cw, ch, fx, fy, fw, fh = cam
    return fx + (x - x0) / cw * fw, fy + (y - y0) / ch * fh


def hl(fr, cam, rect, t, color=YEL, width=6, pad=10):
    """Resalta un rectángulo (px CSS) con un contorno animado."""
    x1, y1 = m2o(cam, rect[0], rect[1])
    x2, y2 = m2o(cam, rect[2], rect[3])
    fx, fy, fw, fh = cam[4:8]
    x1, y1 = max(x1, fx + pad + 8), max(y1, fy + pad + 8)
    x2, y2 = min(x2, fx + fw - pad - 8), min(y2, fy + fh - pad - 8)
    if x2 <= x1 or y2 <= y1:
        return
    d = ImageDraw.Draw(fr, "RGBA")
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    w = int(width + 2 * pulse)
    d.rounded_rectangle((x1 - pad - 4, y1 - pad - 4, x2 + pad + 4, y2 + pad + 4), 20, outline=color + (70,), width=w + 8)
    d.rounded_rectangle((x1 - pad, y1 - pad, x2 + pad, y2 + pad), 16, outline=color + (255,), width=w)


def caption(fr, text, t, t0, t1, y=968, icon=None):
    a = eo((t - t0) / 0.4) * (1 - eio((t - (t1 - 0.4)) / 0.4))
    if a <= 0.01:
        return
    sp = tsp(text, 36, WHITE, True)
    w = sp.width + 90 + (0 if not icon else 20)
    h = 76
    x = W / 2 - w / 2
    yy = y + (1 - eo((t - t0) / 0.4)) * 30
    card(fr, x, yy, w, h, a, 1.0, r=38, fill=BLACK, line=None, shadow=True)
    d = ImageDraw.Draw(fr)
    d.ellipse((x + 30, yy + h / 2 - 8, x + 46, yy + h / 2 + 8), fill=YEL)
    put(fr, sp, x + 62, yy + 12, a)


# ------------------------------------------------------------------ escena 1: portada
def scene1(t):
    n = N[1]
    fr = base("Ingeniería de Soluciones con IA")
    for k, line in enumerate(["Agente de", "despacho y rutas"]):
        a = eo((t - 0.4 - 0.2 * k) / 0.8)
        put(fr, tsp(line, 104, BLACK, True), 100, 250 + k * 128 + (1 - a) * 60, a)
    a = eo((t - 1.5) / 0.7)
    put(fr, tsp("Transportes Cordillera", 50, BLACK), 106, 545 + (1 - a) * 30, a)
    chips = [("inteligencia", "Inteligencia artificial"), ("transporte", "Empresa de transporte"), ("entregas", "Entregas organizadas")]
    x = 106
    for key, label in chips:
        t0 = n.cue(key, default=3.0)
        a = eob((t - t0) / 0.5)
        if a > 0:
            w = pill(fr, x, 690 + (1 - clamp(a)) * 24, label, 28, YEL if key == "inteligencia" else SOFT, BLACK, a=clamp(a))
            x += w + 20
        ev(1, t0, "pop", 0.5)
    # robot con entrada y flotación
    a = eo((t - 0.3) / 1.0)
    s = lerp(0.82, 1.0, eo((t - 0.3) / 1.1))
    fl = math.sin(t * 2.0) * 14
    rb = ROBOT1.resize((int(ROBOT1.width * 0.72), int(ROBOT1.height * 0.72)), Image.LANCZOS)
    put(fr, rb, 1480, 560 + fl + (1 - a) * 40, a, s, center=True)
    return fr


ev(1, 0.25, "whoosh", 0.55)
ev(1, 1.0, "chime", 0.5)


# ------------------------------------------------------------------ escena 2: el problema
def scene2(t):
    n = N[2]
    fr = base("El problema")
    title(fr, "Los imprevistos del reparto", t, 0.1)
    cards = [("avería", "truck", "Avería de un camión", "Sus entregas quedan\nsin conductor."),
             ("importante", "crown", "Cliente VIP urgente", "Pide que su pedido\nllegue antes."),
             ("falla", "box", "Entrega fallida", "El cliente no estaba y\nla entrega no se completa.")]
    for k, (key, ic, head, body) in enumerate(cards):
        t0 = n.cue(key, default=2 + 3 * k)
        p = eob((t - t0) / 0.55)
        a = clamp(p)
        x = 150 + k * 560
        y = 290 + (1 - a) * 40
        if a > 0:
            card(fr, x, y, 500, 440, a, lerp(0.9, 1.0, clamp(p)))
            put(fr, icon_sp(ic, 150), x + 40, y + 40, a)
            put(fr, tsp(head, 40, BLACK, True), x + 40, y + 235, a)
            for j, ln in enumerate(body.split("\n")):
                put(fr, tsp(ln, 29, GRAY), x + 40, y + 310 + j * 44, a)
            # insignia de alerta
            if (t - t0) > 0.5:
                b = eob((t - t0 - 0.5) / 0.4)
                ImageDraw.Draw(fr).ellipse((x + 430, y + 28, x + 470, y + 68), fill=RED)
                put(fr, tsp("!", 30, WHITE, True), x + 450, y + 36, clamp(b), center=True)
        ev(2, t0, "pop", 0.6, -0.4 + 0.4 * k)
    for key, label, fill, col, xx in (("reorganizar", "Hacerlo a mano toma tiempo", YEL, BLACK, 330),
                                      ("tarde", "Los clientes se enteran tarde", BLACK, WHITE, 1010)):
        t0 = n.cue(key, default=9.0)
        a = eob((t - t0) / 0.5)
        if a > 0:
            pill(fr, xx, 810 + (1 - clamp(a)) * 30, label, 32, fill, col, a=clamp(a), h=74)
    return fr


# ------------------------------------------------------------------ escena 3: el panel real
def scene3(t):
    n = N[3]
    fr = base("El panel web")
    t_start = n.cue("escribe", default=2.0)
    t_type = n.cue("ejemplo", default=5.5)
    t_end_voice = n.cue("averió", default=9.0, end=True)
    t_click = t_end_voice + 0.9
    a_in = eo((t - 0.15) / 0.7)
    # cámara: vista general -> consola
    k = eio((t - (t_start - 0.3)) / 1.3)
    cx, cy, cw = lerp(960, 770, k), lerp(540, 520, k), lerp(1920, 880, k)
    cam = shot_frame(fr, "A_limpio", cx, cy, cw)
    # mensaje escrito (sobre la caja de texto)
    s = (cam[6] / cam[2])
    msg = "A las 11:00 el camión 3 se averió"
    typed = int(clamp((t - t_type) / max(0.8, (t_click - 0.7 - t_type))) * len(msg))
    if t >= t_type - 0.05:
        x1, y1 = m2o(cam, 485, 508)
        x2, y2 = m2o(cam, 890, 546)
        d = ImageDraw.Draw(fr)
        d.rectangle((x1, y1, x2, y2), fill=WHITE)
        fz = int(15.5 * s)
        txt = msg[:typed]
        d.text((x1 + 2, (y1 + y2) / 2), txt, font=F(fz, ui=True), fill=(16, 18, 38), anchor="lm")
        if int(t * 2.2) % 2 == 0 and t < t_click:
            tw = d.textlength(txt, font=F(fz, ui=True))
            d.rectangle((x1 + 4 + tw, (y1 + y2) / 2 - fz * 0.62, x1 + 6 + tw, (y1 + y2) / 2 + fz * 0.62), fill=(16, 18, 38))
        if typed != getattr(scene3, "_last", -1):
            scene3._last = typed
    # puntero y clic en "Enviar al agente"
    bx, by = m2o(cam, 990, 523)
    if t > t_click - 1.1:
        p = eio((t - (t_click - 1.1)) / 1.0)
        px, py = lerp(bx + 220, bx, p), lerp(by + 160, by, p)
        press = clamp((t - t_click) / 0.15) * (1 - clamp((t - t_click - 0.15) / 0.25))
        if t >= t_click:
            ring = eo((t - t_click) / 0.7)
            d2 = ImageDraw.Draw(fr, "RGBA")
            r = 20 + 110 * ring
            d2.ellipse((bx - r, by - r, bx + r, by + r), outline=YEL + (int(255 * (1 - ring)),), width=8)
            d2.rounded_rectangle((bx - 92 * s / 1.6, by - 25 * s / 1.6, bx + 92 * s / 1.6, by + 25 * s / 1.6), 18,
                                 fill=(0, 0, 0, int(80 * press)))
        put(fr, pointer_sp(), px + 2 * press, py + 3 * press, 1.0, 1.0 + 0.5 * (1 - press) * 0 + 0.7)
    if t > t_start:
        caption(fr, "El despachador escribe con palabras normales", t, t_start, t_click - 0.4)
    if t > t_click + 0.1:
        caption(fr, "El agente se pone a trabajar…", t, t_click + 0.1, t_click + 3.0)
    ev(3, t_click, "click", 0.9)
    ev(3, t_click + 0.15, "success", 0.35)
    ev(3, t_type, "tick", 0.0)
    return fr


def _typing_ticks():
    n = N[3]
    t_type = n.cue("ejemplo", default=5.5)
    t_click = n.cue("averió", default=9.0, end=True) + 0.9
    msg = 33
    span = max(0.8, t_click - 0.7 - t_type)
    for k in range(msg):
        if k % 2 == 0:
            ev(3, t_type + span * k / msg, "tick", 0.5)


_typing_ticks()


# ------------------------------------------------------------------ escena 4: el flujo del agente
BOX_W, BOX_H, BOX_GAP, BOX_X0, BOX_Y = 210, 140, 38, 111, 330
STEPS = [("Mensaje\nrecibido", None), ("Entender\nel mensaje", "entiende"), ("Recordar\ncasos", "recuerda"),
         ("Decidir\nqué hacer", "decide"), ("Planificar\nentregas", "planifica"), ("Revisar\nel plan", "revisa"),
         ("Ejecutar\ny avisar", None)]


def _arrow(d, x1, y, x2, p, color=BLACK):
    xe = lerp(x1, x2, clamp(p))
    d.line((x1, y, xe, y), fill=color, width=6)
    if p > 0.85:
        d.polygon([(x2, y), (x2 - 18, y - 12), (x2 - 18, y + 12)], fill=color)


def _poly(d, pts, p, color, head=True):
    """Dibuja una polilínea de forma progresiva (p de 0 a 1) con punta de flecha al final."""
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    lens = [math.dist(a, b) for a, b in segs]
    goal = sum(lens) * clamp(p)
    for (a, b), ln in zip(segs, lens):
        take = min(ln, goal)
        if take <= 0:
            break
        e = (a[0] + (b[0] - a[0]) * take / ln, a[1] + (b[1] - a[1]) * take / ln)
        d.line((a, e), fill=color, width=5)
        goal -= take
    if head and p >= 0.98:
        a, b = segs[-1]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        d.polygon([b, (b[0] - 20 * math.cos(ang - 0.45), b[1] - 20 * math.sin(ang - 0.45)),
                   (b[0] - 20 * math.cos(ang + 0.45), b[1] - 20 * math.sin(ang + 0.45))], fill=color)


def scene4(t):
    n = N[4]
    fr = base("Cómo decide el agente")
    title(fr, "El camino de cada mensaje", t, 0.1, y=165, sz=70)
    d = ImageDraw.Draw(fr)
    cues = []
    for k, (label, key) in enumerate(STEPS):
        if k == 0:
            cues.append(0.6)
        elif k == 6:
            cues.append(n.cue("supervisor", default=14.0) + 0.6)
        else:
            cues.append(n.cue(key, default=2 + 2 * k))
    # índice del paso activo = el último cuyo cue ya ocurrió (los dos primeros solapan)
    active = max([k for k, c in enumerate(cues) if t >= c] or [0])
    for k, (label, key) in enumerate(STEPS):
        x = BOX_X0 + k * (BOX_W + BOX_GAP)
        ev(4, cues[k], "pop", 0.5 if k == 0 else 0.55)
        p = eob((t - cues[k]) / 0.5)
        if p <= 0:
            continue
        a = clamp(p)
        is_active = (k == active and t < cues[min(k + 1, 6)] + 0.3) or (k == 6 and t >= cues[6])
        s = lerp(0.85, 1.0, clamp(p)) * (1.07 if (k == active) else 1.0)
        fill = YEL if k == active else (255, 255, 255)
        card(fr, x, BOX_Y, BOX_W, BOX_H, a, s, r=26, fill=fill, line=BLACK, shadow=True, lw=3)
        for j, ln in enumerate(label.split("\n")):
            put(fr, tsp(ln, 30, BLACK, k == active), x + BOX_W / 2, BOX_Y + 48 + j * 40, a, s, center=True)
        put(fr, tsp(str(k + 1), 24, GRAY, True), x + 16, BOX_Y - 38, a)
        if k < 6:
            pa = clamp((t - cues[k + 1] + 0.1) / 0.3)
            _arrow(d, x + BOX_W + 4, BOX_Y + BOX_H / 2, x + BOX_W + BOX_GAP - 4, pa)
    # revisión: qué comprueba (peso, horarios, turnos)
    t_peso = n.cue("peso", default=9.0)
    a = eo((t - t_peso + 0.5) / 0.5)
    put(fr, tsp("Revisa:", 30, GRAY, True), 111, 575, a)
    xcur = 270
    for j, (key, label) in enumerate((("peso", "Peso"), ("horarios", "Horarios"), ("turnos", "Turnos"))):
        t0 = n.cue(key, default=9 + j)
        a = eob((t - t0) / 0.45)
        ev(4, t0, "tick", 0.7)
        w = tsp(label, 28, INDIGO, True).width + 60
        if a > 0:
            pill(fr, xcur, 556, label, 28, INDIGO_SOFT, INDIGO, a=clamp(a), h=56)
        xcur += w + 16
    # salidas alternativas
    cx_rev = BOX_X0 + 5 * (BOX_W + BOX_GAP) + BOX_W / 2
    y_bot = BOX_Y + BOX_H
    t_corr, t_sup = n.cue("corrige", default=13.0), n.cue("supervisor", default=14.5)
    for tt, x, label in ((t_corr, 1100, "Corregir el plan\n(hasta 3 veces)"), (t_sup, 1500, "Avisar al\nsupervisor")):
        a = eob((t - tt) / 0.5)
        ev(4, tt, "pop", 0.6)
        if a > 0:
            card(fr, x, 660, 300, 150, clamp(a), lerp(0.9, 1.0, clamp(a)), r=26, fill=YEL_SOFT, line=BLACK, shadow=True, lw=3)
            for j, ln in enumerate(label.split("\n")):
                put(fr, tsp(ln, 30, BLACK, True), x + 150, 710 + j * 40, clamp(a), center=True)
    orange, red = (180, 100, 0), (190, 45, 45)
    a1 = clamp((t - t_corr + 0.2) / 0.5)
    if a1 > 0:
        pts = [(cx_rev, y_bot + 6), (cx_rev, 610), (1250, 610), (1250, 652)]
        _poly(d, pts, a1, orange)
        put(fr, tsp("si algo no cuadra", 24, orange), cx_rev + 16, 505, a1)
        _poly(d, [(1170, 656), (1170, y_bot + 14)], clamp((t - t_corr - 0.4) / 0.5), orange, head=True)
        put(fr, tsp("reintenta", 24, orange), 1040, 540, clamp((t - t_corr - 0.5) / 0.4))
    a2 = clamp((t - t_sup + 0.2) / 0.5)
    if a2 > 0:
        _poly(d, [(cx_rev, 610), (1650, 610), (1650, 652)], a2, red)
        put(fr, tsp("sin solución", 24, red), 1560, 565, a2)
    # leyenda inferior
    a = eo((t - 1.0) / 0.6)
    put(fr, tsp("Las decisiones importantes las toman reglas claras y verificables.", 34, GRAY), W / 2, 980, a, center=True)
    return fr


# ------------------------------------------------------------------ escena 5: resultado en el panel
def scene5(t):
    n = N[5]
    fr = base("El resultado")
    t_a = n.cue("averiado", default=1.8)
    t_b = n.cue("afectados", default=6.0)
    t_c = n.cue("razonamiento", default=9.0)
    keys = [(0.0, 1078, 330, 1560), (t_a - 0.2, 1078, 1190, 1300), (t_b - 0.2, 1078, 1640, 1320), (t_c - 0.2, 1424, 690, 800)]
    cx, cy, cw = keys[0][1:]
    for i in range(1, len(keys)):
        k = eio((t - keys[i][0]) / 1.1)
        cx, cy, cw = lerp(cx, keys[i][1], k), lerp(cy, keys[i][2], k), lerp(cw, keys[i][3], k)
    cam = shot_frame(fr, "C_averia_full", cx, cy, cw)
    if t_a <= t < t_b:
        hl(fr, cam, (454, 1204, 1704, 1262), t)
        caption(fr, "Camión 3 averiado: sus entregas se reasignan", t, t_a, t_b)
    if t_b <= t < t_c:
        hl(fr, cam, (426, 1731, 1730, 1995), t)
        caption(fr, "9 avisos redactados para los clientes", t, t_b, t_c)
    if t >= t_c:
        lines = [(1117, 468, 1672, 520), (1117, 530, 1672, 580), (1117, 590, 1672, 667), (1117, 796, 1672, 848)]
        hl(fr, cam, lines[int((t - t_c) / 1.15) % len(lines)], t)
        caption(fr, "Razonamiento paso a paso", t, t_c, t_c + 5.5)
    if t < t_a:
        hl(fr, cam, (426, 173, 1730, 392), t)
        caption(fr, "Panel tras la avería: 4 de 5 camiones operativos", t, 0.4, t_a)
    ev(5, t_a, "whoosh", 0.35)
    ev(5, t_b, "whoosh", 0.35)
    ev(5, t_c, "whoosh", 0.35)
    ev(5, t_a + 0.6, "pop", 0.5)
    ev(5, t_b + 0.6, "pop", 0.5)
    return fr


# ------------------------------------------------------------------ escena 6: memoria
def scene6(t):
    n = N[6]
    fr = base("Memoria del agente")
    title(fr, "Dos memorias", t, 0.1, y=150, sz=70)
    t_s, t_l = n.cue("corta", default=2.2), n.cue("larga", default=4.4)
    for k, (tt, ic, head, body) in enumerate(((t_s, "book", "Memoria corta", "Lo que pasó hoy"),
                                              (t_l, "archive", "Memoria larga", "Casos pasados,\nbuscados por significado"))):
        p = eob((t - tt) / 0.55)
        a = clamp(p)
        if a > 0:
            y = 270 + k * 300 + (1 - a) * 30
            card(fr, 96, y, 640, 255, a, lerp(0.92, 1.0, a))
            put(fr, icon_sp(ic, 120), 132, y + 40, a)
            put(fr, tsp(head, 38, BLACK, True), 280, y + 52, a)
            for j, ln in enumerate(body.split("\n")):
                put(fr, tsp(ln, 28, GRAY), 280, y + 118 + j * 40, a)
        ev(6, tt, "pop", 0.6, -0.3)
    # captura de la búsqueda (derecha)
    t_q, t_r = n.cue("escribes", default=7.0), n.cue("encuentra", default=10.0)
    a = eo((t - 0.6) / 0.7)
    fw, fh = 1060, 700
    sx, sy = 800, 250
    cam = None
    img = SHOTS["D_busqueda"]
    if a > 0:
        cx, cy, cw = 900, 470, 980
        x0, y0 = cx - cw / 2, cy - cw * fh / fw / 2
        ch = cw * fh / fw
        reg = img.resize((fw, fh), Image.BILINEAR, box=(x0 * 2, y0 * 2, (x0 + cw) * 2, (y0 + ch) * 2))
        mask = Image.new("L", (fw * 2, fh * 2), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw * 2 - 1, fh * 2 - 1), 52, fill=255)
        mask = mask.resize((fw, fh), Image.LANCZOS)
        cam = (x0, y0, cw, ch, sx, sy, fw, fh)
        d = ImageDraw.Draw(reg)
        sc = fw / cw
        # texto de la consulta: se borra y se escribe de nuevo
        qx1, qy1 = (490 - x0) * sc, (312 - y0) * sc
        qx2, qy2 = (1500 - x0) * sc, (343 - y0) * sc
        q = "se me rompió una rueda del camión"
        shown = int(clamp((t - t_q) / 1.4) * len(q)) if t >= t_q else 0
        if t < t_r:
            d.rectangle((qx1, qy1, qx2, qy2), fill=WHITE)
            if shown:
                d.text((qx1, (qy1 + qy2) / 2), q[:shown], font=F(int(15.5 * sc), ui=True), fill=(16, 18, 38), anchor="lm")
            # resultados ocultos hasta que se "busca"
            d.rectangle((0, (420 - y0) * sc, fw, fh), fill=WHITE)
        else:
            p = eio((t - t_r) / 0.9)
            d.rectangle((0, lerp((420 - y0) * sc, fh, p), fw, fh), fill=WHITE)
        card(fr, sx, sy, fw, fh, a, 1.0, r=26, fill=WHITE, line=LINE)
        fr.paste(reg, (sx, sy), mask)
        if t >= t_r + 0.6:
            hl(fr, cam, (446, 433, 1360, 525), t, pad=6)
            b = eob((t - t_r - 0.9) / 0.45)
            if b > 0:
                pill(fr, 1130, 985, "68 % de parecido · umbral 60 %", 30, GREEN, WHITE, a=clamp(b), h=64)
    for k in range(int(1.4 * 12)):
        ev(6, t_q + k * 0.1, "tick", 0.5) if k % 2 == 0 else None
    ev(6, t_r, "click", 0.8)
    ev(6, t_r + 0.9, "success", 0.4)
    return fr


# ------------------------------------------------------------------ escena 7: IA y reglas
def scene7(t):
    n = N[7]
    fr = base("IA y reglas")
    title(fr, "Cada parte hace lo que mejor sabe", t, 0.1, y=150, sz=62)
    t_i, t_r = n.cue("inteligencia", default=0.8), n.cue("reglas", default=6.0)
    t_ok = n.cue("así", default=9.5)
    for k, (tt, ic, head, items, col) in enumerate(((t_i, "brain", "La IA interpreta", ["Entiende los mensajes", "Redacta los avisos"], INDIGO_SOFT),
                                                    (t_r, "gear", "Las reglas deciden", ["Prioridades y plan", "Peso, horarios y turnos", "Verifican a la IA"], YEL_SOFT))):
        p = eob((t - tt) / 0.6)
        a = clamp(p)
        if a > 0:
            x = 120 + k * 880
            y = 250 + (1 - a) * 40
            card(fr, x, y, 800, 390, a, lerp(0.93, 1.0, a), fill=WHITE)
            put(fr, icon_sp(ic, 130), x + 40, y + 36, a)
            put(fr, tsp(head, 46, BLACK, True), x + 200, y + 56, a)
            for j, it in enumerate(items):
                ta = clamp((t - tt - 0.35 - 0.3 * j) / 0.35)
                d = ImageDraw.Draw(fr)
                put(fr, tsp(it, 34, BLACK), x + 100, y + 190 + j * 62, ta)
                if ta > 0:
                    d.ellipse((x + 44, y + 205 + j * 62, x + 66, y + 227 + j * 62), fill=YEL)
        ev(7, tt, "pop", 0.6, -0.3 + 0.6 * k)
    # flecha de corrección
    a = eob((t - t_ok) / 0.5)
    ev(7, t_ok, "pop", 0.6)
    if a > 0:
        pill(fr, 640, 685, "Si el modelo se equivoca, las reglas lo corrigen", 32, BLACK, WHITE, a=clamp(a), h=72)
    # métricas
    stats = [(n.cue("cincuenta", default=11.5), 57, "", "pruebas automáticas"), (n.cue("automáticas", default=13.0) + 0.2, 9, "", "escenarios con evidencia"),
             (n.cue("gratuitas", default=15.0) - 0.8, 0, "$", "herramientas gratuitas")]
    for k, (tt, val, pre, label) in enumerate(stats):
        p = eob((t - tt) / 0.55)
        a = clamp(p)
        if a > 0:
            x = 210 + k * 520
            y = 790 + (1 - a) * 40
            card(fr, x, y, 480, 220, a, lerp(0.92, 1.0, a), fill=BLACK if k == 0 else WHITE, line=None if k == 0 else LINE)
            c = eo((t - tt) / 1.0)
            shown = pre + str(int(round(val * c)))
            put(fr, tsp(shown, 96, YEL if k == 0 else BLACK, True), x + 40, y + 20, a)
            put(fr, tsp(label, 30, WHITE if k == 0 else GRAY), x + 40, y + 150, a)
        ev(7, tt, "pop", 0.6, -0.3 + 0.3 * k)
    return fr


# ------------------------------------------------------------------ escena 8: cierre
def scene8(t):
    n = N[8]
    fr = base("Gracias")
    a = eo((t - 0.3) / 0.8)
    put(fr, tsp("¡Gracias!", 200, BLACK), 100, 250 + (1 - a) * 50, a)
    a2 = eo((t - 1.4) / 0.7)
    put(fr, tsp("Agente de despacho y rutas", 50, BLACK, True), 108, 540 + (1 - a2) * 30, a2)
    put(fr, tsp("Transportes Cordillera · Evaluación Parcial N°2 · ISY0101", 32, GRAY), 108, 625 + (1 - a2) * 30, a2)
    t3 = n.cue("asistente", default=0.8)
    a3 = eob((t - t3) / 0.5)
    for k, (lab, f) in enumerate((("Confiable", YEL), ("Probado", SOFT), ("Fácil de usar", SOFT))):
        pill(fr, 108 + (0 if k == 0 else (200 if k == 1 else 400)), 735 + (1 - clamp(a3)) * 24, lab, 30, f, BLACK, a=clamp(a3))
    a4 = eo((t - 0.2) / 1.0)
    fl = math.sin(t * 1.9) * 12
    rb = ROBOT2.resize((int(ROBOT2.width * 0.74), int(ROBOT2.height * 0.74)), Image.LANCZOS)
    put(fr, rb, 1500, 560 + fl + (1 - a4) * 50, a4, lerp(0.85, 1.0, a4), center=True)
    # desvanecido final a blanco
    total = n.dur
    fade = clamp((t - (total - 1.1)) / 1.0)
    if fade > 0:
        fr = Image.blend(fr, Image.new("RGB", (W, H), WHITE), fade)
    return fr


ev(8, 0.3, "chime", 0.55)
ev(8, 0.3, "whoosh", 0.4)

SCENES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8]
TRANS = ["band", "push", "band", "fade", "push", "band", "fade"]


# ------------------------------------------------------------------ línea de tiempo
def timeline():
    durs = [N[i].dur for i in range(1, 9)]
    extra = TARGET - (sum(durs) - OVERLAP * 7)
    if extra > 0:       # reparte el tiempo sobrante en las colas (pausas de respiro)
        for i in range(1, 8):
            N[i].tail += extra * 0.5 / 7
        N[8].tail += extra * 0.5
        for i in range(1, 9):
            N[i].dur = N[i].lead + N[i].voice + N[i].tail
    starts, t = [], 0.0
    for i in range(1, 9):
        starts.append(t)
        t += N[i].dur - OVERLAP
    total = starts[-1] + N[8].dur
    return starts, total


STARTS, TOTAL = timeline()


def render_scene(i, T):
    return SCENES[i](T - STARTS[i])


def transition(a, b, p, kind):
    p = clamp(p)
    if kind == "fade":
        return Image.blend(a, b, eio(p))
    if kind == "push":
        s = int(eio(p) * W)
        out = Image.new("RGB", (W, H), WHITE)
        out.paste(a, (-s, 0))
        out.paste(b, (W - s, 0))
        ImageDraw.Draw(out).rectangle((W - s - 6, 0, W - s, H), fill=YEL)
        return out
    # band: franja amarilla inclinada que revela la siguiente escena
    bpos = int(eio(p) * (W + 420)) - 210
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([(0, 0), (bpos + 80, 0), (bpos - 80, H), (0, H)], fill=255)
    out = Image.composite(b, a, mask)
    ImageDraw.Draw(out).polygon([(bpos + 80, 0), (bpos + 150, 0), (bpos - 10, H), (bpos - 80, H)], fill=YEL)
    return out


def frame_at(T):
    i = max(k for k in range(8) if T >= STARTS[k])
    if i > 0 and T < STARTS[i] + OVERLAP:      # transición: cola de la escena anterior + inicio de la nueva
        return transition(render_scene(i - 1, T), render_scene(i, T), (T - STARTS[i]) / OVERLAP, TRANS[i - 1])
    return render_scene(i, T)


def register_events():
    for i in range(1, 9):       # al renderizar cada escena casi al final se registran todos sus efectos
        SCENES[i - 1](N[i].dur - 0.05)


def build_audio(path):
    register_events()
    voices = []
    for i in range(1, 9):
        with wave.open(str(HERE / "audio" / f"s{i:02d}.wav")) as w:
            raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        voices.append((STARTS[i - 1] + N[i].lead, raw))
    events = []
    for (i, t, name), (g, pan) in EVENTS.items():
        if g > 0:
            events.append((STARTS[i - 1] + t, name, g * 0.5, pan))
    for k in range(7):     # whoosh de cada transición
        events.append((STARTS[k + 1] - 0.05, "whoosh", 0.28, 0.0))
    mix = sound.mix_all(TOTAL + 0.5, voices, events)
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sound.SR)
        w.writeframes(pcm.tobytes())


def main(mode):
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    if mode == "stills":
        st = HERE / "stills"
        st.mkdir(exist_ok=True)
        pts = []
        for i in range(8):
            d = N[i + 1].dur
            for f in (0.25, 0.5, 0.8):
                pts.append((i, STARTS[i] + f * (d - OVERLAP)))
        for k in range(7):
            pts.append((100 + k, STARTS[k + 1] + OVERLAP * 0.5))
        register_events()
        for tag, T in pts:
            frame_at(T).save(st / f"{tag:03d}_{T:06.2f}.png")
        print("stills:", len(pts), "· duración total %.1f s" % TOTAL)
        return
    audio = out / "mezcla.wav"
    build_audio(audio)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    mp4 = out / "Agente_Despacho_Video.mp4"
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(audio), "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nframes = int(TOTAL * FPS)
    t0 = time.time()
    for k in range(nframes):
        proc.stdin.write(frame_at(k / FPS).tobytes())
        if k % 150 == 0:
            el = time.time() - t0
            print(f"frame {k}/{nframes}  ({el:.0f}s, quedan ~{el / (k + 1) * (nframes - k):.0f}s)", flush=True)
    proc.stdin.close()
    proc.wait()
    print("Video:", mp4, "· %.1f s" % TOTAL)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "stills")
