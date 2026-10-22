"""Genera la presentación del proyecto sobre la plantilla del Duoc UC (Canva · Poppins).

Reutiliza de la plantilla: portada, logo, ilustraciones del robot y diapositiva de cierre;
el resto de las diapositivas se construye con formas nativas editables en su mismo estilo.

    python scripts/build_presentacion.py --template "<ruta a la plantilla .pptx>"
"""
import argparse
import copy
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "presentacion" / "Presentacion_EP2_Cordillera.pptx"

BLACK = RGBColor(0x1B, 0x1B, 0x1B)
YELLOW = RGBColor(0xE5, 0xAE, 0x38)
YELLOW_SOFT = RGBColor(0xFB, 0xF0, 0xD6)
GRAY = RGBColor(0x6B, 0x6B, 0x6B)
LINE = RGBColor(0xDC, 0xDC, 0xDC)
SOFT = RGBColor(0xF5, 0xF5, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x2E, 0x9E, 0x5B)
RED = RGBColor(0xD6, 0x45, 0x45)
FONT, FONT_B = "Poppins", "Poppins Bold"

NAME_1 = "Fabián Armijo"
NAME_2 = "[Nombre del segundo integrante]"
TEACHER = "[Nombre del docente]"

prs: Presentation
TPL: list = []   # diapositivas originales de la plantilla


# ------------------------------------------------------------------ utilidades de texto
def _runs(par, text, size, color, bold=False):
    """Agrega runs a un párrafo; **negritas** simples."""
    parts = []
    for chunk in text.split("**"):
        parts.append(chunk)
    for i, chunk in enumerate(parts):
        if not chunk:
            continue
        r = par.add_run()
        r.text = chunk
        is_b = bold or (i % 2 == 1)
        r.font.name = FONT_B if is_b else FONT
        r.font.bold = is_b
        r.font.size = Pt(size)
        r.font.color.rgb = color


def _bullet(par, size):
    pPr = par._p.get_or_add_pPr()
    pPr.set("marL", str(int(Pt(size) * 1.1)))
    pPr.set("indent", str(-int(Pt(size) * 1.1)))
    for tag in ("a:buNone", "a:buChar", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu_font = pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"})
    bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
    pPr.append(bu_font)
    pPr.append(bu)


def add_text(slide, x, y, w, h, paras, size=22, color=BLACK, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, bullets=False, space_after=8, line=1.12, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(paras, str):
        paras = [paras]
    for i, t in enumerate(paras):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = align
        par.line_spacing = line
        par.space_after = Pt(space_after)
        _runs(par, t, size, color, bold)
        if bullets:
            _bullet(par, size)
    return tb


def add_card(slide, x, y, w, h, fill=WHITE, line=LINE, radius=0.05, name=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = radius
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1.25)
    sh.shadow.inherit = False
    if name:
        sh.name = name
    return sh


def add_badge(slide, x, y, label, size=0.85, fill=BLACK, color=WHITE, font_size=24):
    sh = add_card(slide, x, y, size, size, fill=fill, line=None, radius=0.22)
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    par = tf.paragraphs[0]
    par.alignment = PP_ALIGN.CENTER
    _runs(par, label, font_size, color, bold=True)
    return sh


def add_pill(slide, x, y, w, label, fill=YELLOW, color=BLACK, size=16, h=0.5):
    sh = add_card(slide, x, y, w, h, fill=fill, line=None, radius=0.5)
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    par = tf.paragraphs[0]
    par.alignment = PP_ALIGN.CENTER
    _runs(par, label, size, color, bold=True)
    return sh


# ------------------------------------------------------------------ utilidades de diapositivas
def clone_template_shape(src_slide, shape_name, dst_slide):
    """Copia una forma con imagen (logo, robot) desde la plantilla, reenlazando la imagen."""
    src = next(s for s in src_slide.shapes if s.name == shape_name)
    el = copy.deepcopy(src._element)
    for blip in el.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        part = src_slide.part.related_part(rid)
        blip.set(qn("r:embed"), dst_slide.part.relate_to(part, RT.IMAGE))
        for ext in blip.iter("{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip"):
            ext.getparent().remove(ext)
    el.xpath(".//p:cNvPr")[0].set("id", str(dst_slide.shapes._next_shape_id))
    dst_slide.shapes._spTree.append(el)
    return el


def new_slide(title, notes=""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    clone_template_shape(TPL[3], "Freeform 2", s)   # logo DuocUC
    add_text(s, 2.4, 0.78, 15.0, 1.4, title, size=50, bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, line=1.0, space_after=0, name="Título")
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def set_cell_border(cell, color="DCDCDC", sides=("b",), width=12700):
    tcPr = cell._tc.get_or_add_tcPr()
    for side in ("l", "r", "t", "b"):
        tag = qn(f"a:ln{side.upper()}")
        for el in tcPr.findall(tag):
            tcPr.remove(el)
        ln = tcPr.makeelement(tag, {"w": str(width if side in sides else 0), "cap": "flat", "cmpd": "sng", "algn": "ctr"})
        if side in sides:
            fill = ln.makeelement(qn("a:solidFill"), {})
            clr = fill.makeelement(qn("a:srgbClr"), {"val": color})
            fill.append(clr)
            ln.append(fill)
        else:
            ln.append(ln.makeelement(qn("a:noFill"), {}))
        tcPr.append(ln)


def add_table(slide, x, y, w, col_w, rows, row_h=0.8, size=18, head_size=17):
    gf = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    for attr in ("firstRow", "bandRow"):
        tblPr.set(attr, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None:
        sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"   # sin estilo ni bordes
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h if i else row_h * 0.7)
        for j, txt in enumerate(row):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.18)
            c.margin_top = c.margin_bottom = Inches(0.06)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = BLACK if i == 0 else WHITE
            tf = c.text_frame
            tf.word_wrap = True
            par = tf.paragraphs[0]
            if i == 0:
                _runs(par, txt, head_size, WHITE, bold=True)
            else:
                _runs(par, txt, size, BLACK, bold=(j == 0))
            set_cell_border(c, sides=("b",) if i else ())
    return gf


# ------------------------------------------------------------------ diapositivas
def slide_portada():
    s = TPL[0]
    for sh in s.shapes:
        if sh.name == "TextBox 10":
            r = sh.text_frame.paragraphs[0].runs[0]
            r.text = "Agente de despacho y rutas"
            r.font.size = Pt(88)
        elif sh.name == "TextBox 3":
            r = sh.text_frame.paragraphs[0].runs[0]
            r.text = "Transportes Cordillera"
            r.font.size = Pt(36)
        elif sh.name == "TextBox 4":
            ps = sh.text_frame.paragraphs
            ps[0].runs[0].text = f"Integrantes: {NAME_1} y {NAME_2}"
            ps[2].runs[0].text = f"Docente: {TEACHER}"
        elif sh.name == "Group 5":
            for sub in sh.shapes:
                if sub.has_text_frame and "Gesti" in sub.text_frame.text:
                    sub.text_frame.paragraphs[0].runs[0].text = "Ingeniería de Soluciones con IA"
    for sh in s.shapes:
        if sh.name == "TextBox 4":
            sh.width = Inches(9.6)
        if sh.name == "TextBox 3":
            sh.width = Inches(10.0)
    set_notes(s, "PRESENTA: Fabián Armijo (≈ 20 s). Nos presentamos y decimos de qué trata el proyecto en una frase: "
                 "«Es un agente de inteligencia artificial que ayuda a organizar el reparto diario de una empresa de "
                 "transporte, y cambia su plan cuando algo sale mal».")
    return s


def slide_sintesis():
    s = new_slide("El proyecto en síntesis")
    for i, (head, items) in enumerate([
        ("Nuestro problema", [
            "Los pedidos se asignan **a mano** a los camiones.",
            "Una avería, un cliente VIP urgente o una entrega fallida **descuadran el día**.",
            "Se pierde el contexto y los clientes **no reciben avisos** a tiempo."]),
        ("Nuestra propuesta", [
            "Un agente de IA que **entiende mensajes** escritos con palabras normales.",
            "**Reorganiza** las entregas, **avisa** a los clientes y **recuerda** lo ocurrido.",
            "Pide ayuda a un **supervisor** cuando no puede resolver."]),
    ]):
        x = 1.3 + i * 9.0
        add_card(s, x, 2.7, 8.4, 5.7)
        add_text(s, x + 0.45, 3.0, 7.5, 0.8, head, size=34, bold=True, color=YELLOW)
        add_text(s, x + 0.45, 4.0, 7.5, 4.3, items, size=27, bullets=True, space_after=16)
    for i, (num, lab) in enumerate([("5", "camiones"), ("25", "pedidos al día"), ("10", "clientes"), ("100 %", "datos inventados")]):
        x = 1.3 + i * 4.5
        add_card(s, x, 8.75, 4.1, 1.7, fill=SOFT, line=None)
        add_text(s, x + 0.3, 8.8, 3.5, 0.9, num, size=40, bold=True)
        add_text(s, x + 0.3, 9.72, 3.6, 0.6, lab, size=20, color=GRAY)
    set_notes(s, "PRESENTA: Fabián (≈ 40 s). Problema: en Transportes Cordillera, ficticia, los pedidos se asignan a mano y "
                 "cualquier imprevisto descuadra el día. Propuesta: un agente que entiende mensajes simples y cambia el plan. "
                 "Aclarar que todos los datos son inventados.")
    return s


def slide_arquitectura():
    s = new_slide("Las piezas del sistema")
    img = ROOT / "docs" / "diagramas" / "arquitectura_simple.png"
    add_card(s, 1.0, 2.7, 11.2, 7.8)
    pic = s.shapes.add_picture(str(img), Inches(1.3), Inches(3.0), width=Inches(10.6))
    pic.name = "Diagrama de arquitectura"
    for i, (t, d) in enumerate([
        ("Panel web", "El despachador escribe lo que ocurrió."),
        ("Agente", "Entiende, recuerda, planifica y avisa."),
        ("Apoyos", "Herramientas, memoria y modelo de lenguaje.")]):
        y = 2.7 + i * 2.65
        add_badge(s, 12.7, y + 0.05, str(i + 1))
        add_text(s, 13.85, y, 5.2, 0.7, t, size=30, bold=True)
        add_text(s, 13.85, y + 0.8, 5.2, 1.7, d, size=22, color=GRAY)
    set_notes(s, "PRESENTA: Fabián (≈ 40 s). Seguir el dibujo de arriba hacia abajo: la persona usa un panel web, el panel habla con "
                 "una API, y la API entrega el mensaje al agente. El agente usa herramientas para consultar y escribir, una "
                 "memoria y un modelo de lenguaje. Mencionar que el modelo se puede cambiar: Groq en la nube, Ollama en el "
                 "computador o modo sin IA.")
    return s


def slide_flujo():
    s = new_slide("Cómo decide el agente")
    img = ROOT / "docs" / "diagramas" / "flujo_simple.png"
    add_card(s, 1.0, 2.7, 12.6, 6.4)
    pic = s.shapes.add_picture(str(img), Inches(1.6), Inches(3.05), width=Inches(11.4))
    pic.name = "Diagrama de flujo"
    add_card(s, 14.0, 2.7, 4.9, 6.4, fill=BLACK, line=None)
    add_text(s, 14.4, 3.1, 4.2, 5.8, [
        "La decisión importante la toman **reglas claras** y verificables.",
        "La IA solo **interpreta** mensajes y **redacta** avisos."],
        size=26, color=WHITE, space_after=20)
    add_pill(s, 1.0, 9.5, 6.0, "Si falta un dato, lo pregunta", size=20, h=0.7)
    add_pill(s, 7.3, 9.5, 6.3, "Sin solución, avisa a un supervisor", size=20, h=0.7)
    set_notes(s, "PRESENTA: Fabián (≈ 40 s). El mensaje pasa por pasos: entender, recordar, decidir, planificar, revisar y ejecutar. "
                 "En el camino hay decisiones: si falta un dato lo pregunta, si no entiende avisa a un supervisor, y si el plan no "
                 "cumple las reglas intenta corregirlo hasta tres veces. Idea fuerza: las decisiones importantes las toman reglas "
                 "verificables, no la IA.")
    return s


def slide_herramientas():
    s = new_slide("Herramientas del agente")
    cards = [
        ("1", "Consultar", ["Flota y pedidos del día", "Tráfico y perfil del cliente", "Casos pasados y políticas"]),
        ("2", "Escribir", ["Asignar entregas a camiones", "Hojas de ruta y avisos", "Registrar lo ocurrido"]),
        ("3", "Razonar", ["Entender el mensaje", "Comprobar que camiones y pedidos existen", "Redactar avisos"]),
    ]
    for i, (n, head, items) in enumerate(cards):
        x = 1.3 + i * 5.95
        add_card(s, x, 2.7, 5.5, 6.45)
        add_badge(s, x + 0.45, 3.05, n)
        add_text(s, x + 0.45, 4.15, 4.6, 0.8, head, size=34, bold=True)
        add_text(s, x + 0.45, 5.15, 4.7, 3.9, items, size=26, bullets=True, space_after=12)
    add_pill(s, 1.3, 9.55, 8.4, "Más de veinte herramientas en total", size=22, h=0.75)
    add_text(s, 10.1, 9.62, 8.8, 0.9, "Ejemplo: no se asigna una entrega si el camión no soporta el peso.", size=19, color=GRAY)
    set_notes(s, "PRESENTA: Compañero/a (≈ 30 s). Hay tres tipos de herramientas: las que consultan datos, las que escriben "
                 "(asignar, crear hojas de ruta, avisar) y las que ayudan a razonar. Ejemplo concreto: asignar entregas "
                 "falla si el camión no soporta el peso.")
    return s


def slide_memoria():
    s = new_slide("Memoria: corta y larga")
    add_card(s, 1.2, 2.7, 8.6, 3.75)
    add_text(s, 1.65, 2.95, 7.7, 0.7, "Memoria corta · la jornada", size=27, bold=True, color=YELLOW)
    add_text(s, 1.65, 3.75, 7.8, 2.6, ["Guarda lo ocurrido en el día.", "Sigue ahí aunque se reinicie el programa.",
                                       "Con **3 cambios** en un día, avisa que la jornada está inestable."],
             size=22, bullets=True, space_after=8)
    add_card(s, 1.2, 6.75, 8.6, 3.6)
    add_text(s, 1.65, 7.0, 7.7, 0.7, "Memoria larga · casos pasados", size=27, bold=True, color=YELLOW)
    add_text(s, 1.65, 7.85, 7.8, 2.4, ["Busca por **significado**, no por palabras exactas.",
                                       "Un caso se acepta si supera el **60 %** de parecido."],
             size=22, bullets=True, space_after=8)

    add_card(s, 10.2, 2.7, 8.6, 7.65)
    add_text(s, 10.65, 2.95, 7.8, 1.2, "¿Qué tan parecido es un mensaje a un caso pasado?", size=22, bold=True, space_after=0)
    cd = CategoryChartData()
    cats = ["Cliente ausente en el pedido 8", "Camión 3 averiado en zona norte", "Se me rompió una rueda", "Texto sin relación"]
    vals = [74, 72, 67, 54]
    cd.categories = cats
    cd.add_series("Similitud (%)", vals)
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(10.4), Inches(4.2), Inches(8.2), Inches(5.9), cd)
    gf.name = "Gráfico de similitud"
    ch = gf.chart
    ch.has_legend = False
    ch.has_title = False
    ch.font.name = FONT
    ch.font.size = Pt(16)
    ch.font.color.rgb = BLACK
    plot = ch.plots[0]
    plot.gap_width = 45
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = '0"%"'
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(20)
    dl.font.bold = True
    dl.font.name = FONT_B
    ser = plot.series[0]
    for i, v in enumerate(vals):
        pt = ser.points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = YELLOW if v >= 60 else RGBColor(0xC9, 0xC9, 0xC9)
    ca, va = ch.category_axis, ch.value_axis
    ca.reverse_order = True
    ca.format.line.color.rgb = LINE
    ca.tick_labels.font.size = Pt(16)
    ca.has_major_gridlines = False
    va.minimum_scale, va.maximum_scale = 0, 100
    va.has_major_gridlines = False
    va.visible = False
    set_notes(s, "PRESENTA: Compañero/a (≈ 40 s). Memoria corta: lo que pasó hoy, y sigue disponible si se reinicia. Con tres "
                 "cambios en el día el agente avisa que la jornada está inestable. Memoria larga: busca casos pasados por "
                 "significado. En el gráfico: mensajes parecidos a casos reales superan el 60 %; un texto sin relación queda "
                 "en 54 % y se descarta. Por eso el umbral es 60 %.")
    return s


def slide_planificacion():
    s = new_slide("Planificación y decisiones")
    add_card(s, 1.2, 2.7, 6.2, 7.7, fill=BLACK, line=None)
    add_text(s, 1.65, 3.0, 5.4, 0.9, "Puntaje de urgencia", size=30, bold=True, color=YELLOW)
    add_text(s, 1.65, 4.05, 5.4, 3.8, ["Sube si el cliente es **VIP**.", "Sube si el pedido tiene **prioridad alta**.",
                                       "Sube si queda **poco tiempo** en su ventana horaria."],
             size=26, color=WHITE, bullets=True, space_after=14)
    add_text(s, 1.65, 8.5, 5.4, 1.7, "Nunca se supera el **peso máximo** de un camión.", size=24, color=WHITE)
    add_table(s, 7.8, 2.7, 11.0, [3.4, 7.6], [
        ["Situación", "Qué hace el agente"],
        ["Avería de un camión", "Lo saca del plan, reparte sus entregas y avisa a los clientes."],
        ["Cliente VIP urgente", "Sube el pedido a prioridad máxima y reordena la ruta."],
        ["Entrega fallida", "1.ª vez: reintenta. 2.ª vez: pasa al supervisor."],
        ["Mensaje confuso", "Pide el dato que falta. No inventa información."],
    ], row_h=1.6, size=22, head_size=22)
    set_notes(s, "PRESENTA: Compañero/a (≈ 40 s). Cada pedido recibe un puntaje de urgencia que sube si el cliente es VIP, si "
                 "tiene prioridad alta o si queda poco tiempo. A la derecha, qué hace el agente en cada situación. Remarcar: "
                 "en la entrega fallida no insiste: al segundo intento pasa el caso a un supervisor.")
    return s


def slide_demo():
    s = new_slide("Demostración en vivo")
    steps = [("1", "Inicio de jornada", "Planifica los 25 pedidos"),
             ("2", "Avería del camión 3", "Reasigna sus entregas"),
             ("3", "Cliente VIP urgente", "Pedido 14 antes de las 12:00"),
             ("4", "Entrega fallida", "Reintento y escalamiento"),
             ("5", "Mensaje confuso", "Pide datos; no inventa")]
    for i, (n, a, b) in enumerate(steps):
        y = 2.7 + i * 1.58
        add_card(s, 1.2, y, 7.9, 1.4, fill=SOFT, line=None)
        add_badge(s, 1.45, y + 0.28, n, size=0.85)
        add_text(s, 2.7, y + 0.14, 6.3, 0.65, a, size=26, bold=True)
        add_text(s, 2.7, y + 0.78, 6.3, 0.55, b, size=19, color=GRAY)
    add_card(s, 9.5, 2.7, 9.3, 7.45)
    pic = s.shapes.add_picture(str(ROOT / "docs" / "capturas" / "dashboard.jpg"), Inches(9.7), Inches(2.9), width=Inches(8.9))
    pic.name = "Captura del panel"
    add_text(s, 9.7, 9.45, 8.9, 0.5, "Panel web del agente (captura real)", size=16, color=GRAY, align=PP_ALIGN.CENTER)
    set_notes(s, "PRESENTAN: los dos (≈ 2 min). Abrir el panel en http://127.0.0.1:8000 (ya iniciado con "
                 "python -m uvicorn api.main:app --port 8000). Orden: 1) «Inicio de jornada». 2) «Avería camión 3»: mostrar "
                 "que el camión queda en rojo y el razonamiento paso a paso. 3) «VIP urgente». 4) «Entrega fallida» y luego "
                 "«Segundo fallo». 5) «Evento ambiguo». Si falla internet o Groq: el modo «Reglas» funciona sin conexión. "
                 "Plan B: video de respaldo.")
    return s


def slide_resultados():
    s = new_slide("Resultados y pruebas")
    stats = [("57", "pruebas automáticas, todas pasan"), ("9", "escenarios con evidencia paso a paso"),
             ("20+", "herramientas del agente"), ("$0", "costo: todo gratuito")]
    for i, (n, lab) in enumerate(stats):
        x = 1.2 + i * 4.5
        add_card(s, x, 2.7, 4.2, 3.55, fill=BLACK if i == 0 else WHITE, line=None if i == 0 else LINE)
        add_text(s, x + 0.35, 2.85, 3.6, 1.5, n, size=66, bold=True, color=YELLOW if i == 0 else BLACK)
        add_text(s, x + 0.35, 4.5, 3.6, 1.6, lab, size=20, color=WHITE if i == 0 else GRAY)
    add_table(s, 1.2, 6.65, 17.6, [4.6, 13.0], [
        ["Escenario", "Resultado comprobado"],
        ["Avería a las 11:00", "9 entregas hechas, 16 reasignadas y ninguna en el camión averiado."],
        ["Cliente VIP urgente", "El pedido 14 llega a las 12:00, dentro de su hora límite."],
        ["Entrega fallida", "1.er fallo: reintento. 2.º fallo: pasa a un supervisor."],
    ], row_h=0.98, size=21, head_size=21)
    set_notes(s, "PRESENTA: Compañero/a (≈ 30 s). Datos clave: 57 pruebas automáticas que pasan, 9 escenarios con evidencia "
                 "guardada en el repositorio, más de veinte herramientas y costo cero. Los tres resultados de la tabla "
                 "salen de los escenarios del repositorio (carpeta docs/evidencia).")
    return s


def slide_hallazgo():
    s = new_slide("Un hallazgo que cambió el diseño")
    add_text(s, 1.3, 2.55, 17.4, 0.8, "Mensaje: «Cliente ausente en el pedido 8»", size=30, bold=True, align=PP_ALIGN.CENTER)
    add_card(s, 1.3, 3.65, 8.0, 3.2, fill=WHITE, line=RED)
    add_text(s, 1.75, 3.85, 7.1, 0.7, "Modelo pequeño (IA sola)", size=26, bold=True, color=RED)
    add_text(s, 1.75, 4.7, 7.1, 2.0, ["Entendió: **«inicio de jornada»**", "Habría replanificado todo el día."], size=23, space_after=8)
    add_card(s, 10.7, 3.65, 8.0, 3.2, fill=WHITE, line=GREEN)
    add_text(s, 11.15, 3.85, 7.1, 0.7, "Con reglas de seguridad", size=26, bold=True, color=GREEN)
    add_text(s, 11.15, 4.7, 7.1, 2.0, ["Entendió: **«entrega fallida»**", "Solo reprograma ese pedido."], size=23, space_after=8)
    add_text(s, 9.35, 4.75, 1.3, 0.9, "→", size=48, bold=True, align=PP_ALIGN.CENTER, color=BLACK)
    for i, (n, t) in enumerate([("1", "Las reglas claras tienen prioridad sobre la IA."),
                                ("2", "Se comprueba que los camiones y pedidos existan."),
                                ("3", "Los avisos de la IA se revisan antes de enviarse.")]):
        x = 1.3 + i * 5.95
        add_card(s, x, 7.25, 5.5, 3.1, fill=SOFT, line=None)
        add_badge(s, x + 0.35, 7.5, n, size=0.75, font_size=22)
        add_text(s, x + 0.35, 8.5, 4.9, 1.8, t, size=21)
    set_notes(s, "PRESENTA: Fabián (≈ 40 s). Prueba real con el modelo pequeño que corre en el computador (Qwen2.5 de 1,5 mil "
                 "millones de parámetros): confundió «cliente ausente» con «inicio de jornada», lo que habría replanificado todo "
                 "el día. Lo corregimos con tres medidas y cada una tiene una prueba automática. Esto justifica que las "
                 "decisiones críticas las tomen reglas y no la IA.")
    return s


def slide_componentes():
    s = new_slide("¿Por qué estos componentes?")
    add_table(s, 1.2, 2.7, 17.6, [4.9, 12.7], [
        ["Componente", "Dato que lo respalda"],
        ["LangGraph", "El flujo tiene 4 decisiones y su estado se conserva si se reinicia el programa."],
        ["Reglas + IA", "El modelo pequeño confundió un mensaje; las reglas lo corrigieron."],
        ["Groq y Ollama", "El computador tiene 7,9 GB y no tiene tarjeta gráfica: se usa la nube o un modelo pequeño."],
        ["Memoria por significado", "Casos parecidos: 57 % a 77 %. Texto sin relación: 54 %. Umbral: 60 %."],
        ["Bases de datos livianas", "SQLite y ChromaDB funcionan en cualquier computador, sin servidores."],
    ], row_h=1.3, size=21, head_size=21)
    set_notes(s, "PRESENTAN: los dos (≈ 40 s). Cada integrante explica con sus propias palabras por qué eligió su parte, "
                 "apoyándose en el dato de la columna derecha. Preguntas probables: ¿por qué no dejar todo a la IA? "
                 "(hallazgo); ¿qué pasa si falla internet? (modo Ollama o reglas); ¿cómo se evita que invente un camión? "
                 "(se valida contra la base de datos); ¿cómo escala? (más camiones = más datos, mismo flujo).")
    return s


def slide_limites():
    s = new_slide("Límites y próximos pasos")
    for i, (head, items) in enumerate([
        ("Límites de hoy", ["Datos, mapas y tráfico **simulados**.", "Cada camión hace **una sola carga** al día.",
                            "Los avisos a clientes **se simulan**.", "El modelo pequeño usa mal las herramientas."]),
        ("Próximos pasos", ["Conectar **mapas y tráfico reales**.", "Enviar avisos reales por **correo o mensaje**.",
                            "Usar un **modelo más grande** (Groq).", "Probar con **datos reales** de una empresa."]),
    ]):
        x = 1.3 + i * 9.0
        add_card(s, x, 2.7, 8.4, 7.4)
        add_text(s, x + 0.45, 3.0, 7.5, 0.9, head, size=32, bold=True, color=YELLOW)
        add_text(s, x + 0.45, 4.15, 7.5, 5.8, items, size=29, bullets=True, space_after=18)
    set_notes(s, "PRESENTA: Compañero/a (≈ 20 s). Ser honestos con los límites: es un ejercicio con datos inventados. Los próximos "
                 "pasos son conectar mapas y mensajes reales y probar con datos reales.")
    return s


def slide_gracias():
    s = TPL[17]
    for sh in s.shapes:
        if sh.name == "TextBox 3":
            sh.width = Inches(10.0)
    add_text(s, 1.37, 7.6, 9.5, 1.4, ["¿Preguntas?"], size=44, bold=True)
    set_notes(s, "PRESENTAN: los dos (≈ 10 s). Agradecer y abrir la ronda de preguntas (10 minutos). Tener abierto el repositorio "
                 "y el panel por si piden mostrar código o el razonamiento paso a paso.")
    return s


# ------------------------------------------------------------------ ensamblado
def build(template: Path):
    global prs
    prs = Presentation(str(template))
    TPL[:] = list(prs.slides)
    order = [slide_portada(), slide_sintesis(), slide_arquitectura(), slide_flujo(), slide_herramientas(),
             slide_memoria(), slide_planificacion(), slide_demo(), slide_resultados(), slide_hallazgo(),
             slide_componentes(), slide_limites(), slide_gracias()]
    order_ids = [s.slide_id for s in order]
    keep = set(order_ids)
    lst = prs.slides._sldIdLst
    ids = {int(e.get("id")): e for e in lst}
    for e in list(lst):
        lst.remove(e)
    # quitar las diapositivas de la plantilla que no se usan
    for sid, e in ids.items():
        if sid not in keep:
            prs.part.drop_rel(e.get(qn("r:id")))
    for sid in order_ids:
        lst.append(ids[sid])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    return OUT


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    args = ap.parse_args()
    print("Presentación generada:", build(Path(args.template)))
