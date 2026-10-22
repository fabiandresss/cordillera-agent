"""Genera la guía simple del sistema (PDF) con pantallazos y explicaciones en lenguaje cotidiano.

    python scripts/prepare_guia_images.py     # recortes y números sobre las capturas
    python scripts/build_guia_pdf.py
"""
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "docs" / "guia" / "proc"
DIAG = ROOT / "docs" / "diagramas"
OUT = ROOT / "docs" / "guia" / "Guia_Simple_del_Sistema.pdf"

FONTS = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
pdfmetrics.registerFont(TTFont("Poppins", str(FONTS / "Poppins-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Poppins-Bold", str(FONTS / "Poppins-Bold.ttf")))
pdfmetrics.registerFontFamily("Poppins", normal="Poppins", bold="Poppins-Bold", italic="Poppins", boldItalic="Poppins-Bold")

INDIGO = colors.HexColor("#5046E5")
INDIGO_SOFT = colors.HexColor("#ECEAFD")
YELLOW = colors.HexColor("#E5AE38")
YELLOW_SOFT = colors.HexColor("#FDF3DC")
GREEN_SOFT = colors.HexColor("#E3F6E9")
DARK = colors.HexColor("#1B1B1B")
GRAY = colors.HexColor("#6B6B6B")
LINE = colors.HexColor("#DCDCDC")
SOFT = colors.HexColor("#F4F5FB")

W = A4[0] - 4 * cm   # ancho útil

S = {
    "body": ParagraphStyle("body", fontName="Poppins", fontSize=9.6, leading=15, textColor=DARK, spaceAfter=6),
    "lead": ParagraphStyle("lead", keepWithNext=1, fontName="Poppins", fontSize=9.6, leading=15, textColor=DARK, spaceAfter=6),
    "small": ParagraphStyle("small", fontName="Poppins", fontSize=8.2, leading=12, textColor=GRAY),
    "h1": ParagraphStyle("h1", keepWithNext=1, fontName="Poppins-Bold", fontSize=21, leading=26, textColor=INDIGO, spaceBefore=4, spaceAfter=10),
    "h2": ParagraphStyle("h2", keepWithNext=1, fontName="Poppins-Bold", fontSize=13, leading=18, textColor=DARK, spaceBefore=12, spaceAfter=5),
    "h3": ParagraphStyle("h3", keepWithNext=1, fontName="Poppins-Bold", fontSize=10.5, leading=15, textColor=INDIGO, spaceBefore=6, spaceAfter=3),
    "cap": ParagraphStyle("cap", fontName="Poppins", fontSize=8, leading=11, textColor=GRAY, alignment=TA_CENTER, spaceAfter=10),
    "cell": ParagraphStyle("cell", fontName="Poppins", fontSize=8.8, leading=12.5, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="Poppins-Bold", fontSize=8.8, leading=12.5, textColor=DARK),
    "head": ParagraphStyle("head", fontName="Poppins-Bold", fontSize=8.8, leading=12, textColor=colors.white),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.8, leading=12.5, textColor=DARK),
    "bul": ParagraphStyle("bul", fontName="Poppins", fontSize=9.6, leading=14.5, textColor=DARK, leftIndent=14, bulletIndent=2, spaceAfter=3),
}


def P(t, st="body"):
    return Paragraph(t, S[st])


def bullets(items):
    return [Paragraph(t, S["bul"], bulletText="•") for t in items]


def fig(name, width_cm, caption=None, folder=PROC):
    path = folder / name
    with PILImage.open(path) as im:
        w, h = im.size
    img = Image(str(path), width=width_cm * cm, height=width_cm * cm * h / w)
    box = Table([[img]], colWidths=[width_cm * cm])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    box.hAlign = "CENTER"
    items = [box]
    if caption:
        items += [Spacer(1, 3), P(caption, "cap")]
    return KeepTogether(items)


def table(rows, widths, header=True, zebra=True):
    data = []
    for i, row in enumerate(rows):
        data.append([Paragraph(str(c), S["head"] if (header and i == 0) else (S["cellb"] if j == 0 else S["cell"]))
                     for j, c in enumerate(row)])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
             ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), INDIGO)]
    if zebra:
        for r in range(1 if header else 0, len(rows)):
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), SOFT))
    t.setStyle(TableStyle(style))
    return KeepTogether([t, Spacer(1, 4)]) if len(rows) <= 12 else t


def callout(title, text, bg=INDIGO_SOFT, bar=INDIGO):
    inner = [[Paragraph(f"<b>{title}</b>", ParagraphStyle("ct", parent=S["body"], textColor=bar, spaceAfter=2, fontName="Poppins-Bold")),
              ]] + [[Paragraph(text, S["body"])]]
    t = Table(inner, colWidths=[W - 0.4 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (0, 0), 8), ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
                           ("TOPPADDING", (0, 1), (-1, -1), 0)]))
    return KeepTogether([t, Spacer(1, 8)])


def codebox(lines):
    t = Table([[Paragraph("<br/>".join(lines), S["code"])]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F2F2")), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return KeepTogether([t, Spacer(1, 8)])


def steps(items):
    """Lista numerada con círculos (qué hace el agente, paso a paso)."""
    rows = []
    for i, (title, text) in enumerate(items, 1):
        num = Table([[Paragraph(f"<font color='white'><b>{i}</b></font>", ParagraphStyle("n", fontName="Poppins-Bold", fontSize=9.5, alignment=TA_CENTER, leading=11))]],
                    colWidths=[0.75 * cm], rowHeights=[0.75 * cm])
        num.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), INDIGO), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                 ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        rows.append([num, [Paragraph(f"<b>{title}</b>", S["cell"]), Paragraph(text, S["cell"])]])
    t = Table(rows, colWidths=[1.2 * cm, W - 1.2 * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    return t


# ------------------------------------------------------------------ páginas
def on_page(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont("Poppins", 7.5)
        canvas.setFillColor(GRAY)
        canvas.drawString(2 * cm, A4[1] - 1.2 * cm, "Guía simple del sistema · Agente de despacho y rutas")
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.2 * cm, "Transportes Cordillera (caso de estudio)")
        canvas.setStrokeColor(LINE)
        canvas.line(2 * cm, A4[1] - 1.4 * cm, A4[0] - 2 * cm, A4[1] - 1.4 * cm)
        canvas.drawCentredString(A4[0] / 2, 1.1 * cm, str(doc.page - 1))
    canvas.restoreState()


def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    robot = PROC / "robot.png"
    if robot.exists():
        with PILImage.open(robot) as im:
            w, h = im.size
        rw = 10.5 * cm
        canvas.drawImage(str(robot), A4[0] - rw - 1.2 * cm, 3.0 * cm, width=rw, height=rw * h / w, mask="auto")
    canvas.setFillColor(INDIGO)
    canvas.roundRect(2 * cm, A4[1] - 3.2 * cm, 3.6 * cm, 0.8 * cm, 0.4 * cm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Poppins-Bold", 8.5)
    canvas.drawCentredString(2 * cm + 1.8 * cm, A4[1] - 2.93 * cm, "GUÍA SIMPLE")
    canvas.setFillColor(DARK)
    canvas.setFont("Poppins-Bold", 34)
    canvas.drawString(2 * cm, A4[1] - 6.2 * cm, "Agente de")
    canvas.drawString(2 * cm, A4[1] - 7.7 * cm, "despacho y")
    canvas.drawString(2 * cm, A4[1] - 9.2 * cm, "rutas")
    canvas.setFillColor(YELLOW)
    canvas.rect(2 * cm, A4[1] - 10.3 * cm, 2.2 * cm, 0.18 * cm, stroke=0, fill=1)
    canvas.setFillColor(GRAY)
    canvas.setFont("Poppins", 12)
    canvas.drawString(2 * cm, A4[1] - 11.6 * cm, "Qué es, cómo funciona y cómo usarlo,")
    canvas.drawString(2 * cm, A4[1] - 12.4 * cm, "explicado paso a paso y con pantallazos.")
    canvas.setFillColor(DARK)
    canvas.setFont("Poppins-Bold", 10)
    canvas.drawString(2 * cm, 3.3 * cm, "Transportes Cordillera (caso de estudio)")
    canvas.setFont("Poppins", 9)
    canvas.setFillColor(GRAY)
    canvas.drawString(2 * cm, 2.6 * cm, "Evaluación Parcial N°2 · ISY0101 Ingeniería de Soluciones con IA · Duoc UC")
    canvas.drawString(2 * cm, 2.0 * cm, "Octubre 2026")
    canvas.restoreState()


def story():
    s = []
    s += [PageBreak()]

    # ----------------------------------------------------------- Resumen y contenidos
    s += [P("En una frase", "h1")]
    s += [callout("¿Qué es este sistema?",
                  "Es un <b>asistente de inteligencia artificial que ayuda a coordinar los camiones de reparto</b> de una "
                  "empresa. Tú le cuentas qué pasó con palabras normales, por ejemplo <i>«se averió el camión 3»</i>, y él "
                  "reorganiza el trabajo del día, avisa a los clientes y se acuerda de lo ocurrido.")]
    s += [P("Esta guía está pensada para entender el proyecto sin saber de programación. Primero se explica el problema, "
            "luego cómo funciona por dentro, después se recorre cada pantalla con pantallazos y, al final, hay una guía "
            "para encenderlo y las preguntas más comunes.")]
    s += [P("Contenido", "h2")]
    s += [table([
        ["Capítulo", "De qué trata"],
        ["1. ¿Para qué sirve?", "El problema que resuelve y un ejemplo cotidiano."],
        ["2. El caso de ejemplo", "La empresa inventada con la que se probó el sistema."],
        ["3. ¿Cómo funciona?", "Los pasos que sigue el agente, con un ejemplo real paso a paso."],
        ["4. Las piezas del sistema", "Qué hace cada parte, explicado con comparaciones simples."],
        ["5. Recorrido por el panel", "Cada pantalla con pantallazos y qué hacer en ella."],
        ["6. Cómo probarlo", "Un guion de seis pasos para ver el sistema en acción."],
        ["7. Ideas clave", "Memoria, prioridades, IA frente a reglas y cuándo pide ayuda."],
        ["8. Cómo encenderlo", "Comandos, solución de problemas y mapa de carpetas."],
        ["9. Preguntas frecuentes y glosario", "Respuestas rápidas y significado de las palabras difíciles."],
    ], [5.2, W / cm - 5.2])]

    # ----------------------------------------------------------- 1
    s += [PageBreak(), P("1. ¿Para qué sirve?", "h1")]
    s += [P("Una empresa de transporte reparte pedidos todos los días con varios camiones. Cada pedido tiene un cliente, un "
            "peso y una ventana de horas en la que debe llegar. Alguien tiene que decidir <b>qué camión lleva qué pedido y en "
            "qué orden</b>. Eso se llama <b>despacho</b>.")]
    s += [P("El problema aparece cuando algo sale mal durante el día:")]
    s += bullets(["Un camión <b>se avería</b> y sus entregas quedan sin conductor.",
                  "Un cliente importante (<b>VIP</b>) pide que su pedido llegue antes.",
                  "Una <b>entrega falla</b> porque el cliente no estaba."])
    s += [Spacer(1, 4), table([
        ["Sin el sistema", "Con el sistema"],
        ["Los pedidos se reparten a mano.", "El agente reparte los pedidos según reglas claras."],
        ["Un imprevisto descuadra todo el día.", "El agente reorganiza el plan en segundos."],
        ["Se pierde el contexto de lo que pasó.", "El agente guarda cada caso y lo recuerda después."],
        ["Los clientes se enteran tarde.", "Cada cambio genera un aviso para los clientes afectados."],
        ["Nadie sabe por qué se tomó una decisión.", "El panel muestra el razonamiento paso a paso."],
    ], [W / cm / 2, W / cm / 2])]
    s += [Spacer(1, 8), callout("Una comparación",
                                "Imagina un <b>despachador muy ordenado</b>: nunca olvida un caso anterior, trabaja con una lista de "
                                "reglas claras, sabe leer mensajes escritos y avisa a todos los afectados. Eso es este sistema.",
                                YELLOW_SOFT, YELLOW)]
    s += [callout("Importante", "La empresa, los camiones, los clientes y los pedidos son <b>inventados</b>. Sirven para "
                                "demostrar cómo funciona el agente; el sistema no está conectado a ninguna empresa real.",
                  GREEN_SOFT, colors.HexColor("#2E9E5B"))]

    # ----------------------------------------------------------- 2
    s += [P("2. El caso de ejemplo: Transportes Cordillera", "h1")]
    s += [P("Para probar el sistema se creó una empresa ficticia con estos datos:")]
    s += [table([
        ["Dato", "Valor"],
        ["Camiones", "5 camiones, con capacidades de 800 kg a 3.000 kg y un conductor cada uno."],
        ["Pedidos del día", "25 pedidos, cada uno con peso, zona de entrega y una ventana de horas."],
        ["Clientes", "10 clientes; 3 de ellos son VIP (farmacia, clínica y laboratorio)."],
        ["Zonas", "6 zonas ficticias: Centro, Norte, Sur, Oriente, Poniente e Industrial."],
        ["Jornada", "De 08:00 a 18:00. El sistema usa un reloj simulado que avanza con los mensajes."],
        ["Casos pasados", "15 incidentes antiguos (averías, entregas fallidas…) que el agente puede recordar."],
    ], [3.6, W / cm - 3.6])]
    s += [Spacer(1, 6), P("Sobre este día se simulan tres situaciones: <b>una avería</b>, <b>un cliente VIP urgente</b> y "
                          "<b>una entrega fallida</b>. Más adelante verás cómo reacciona el agente a cada una.")]

    # ----------------------------------------------------------- 3
    s += [Spacer(1, 10), P("3. ¿Cómo funciona?", "h1")]
    s += [P("Cada vez que le escribes un mensaje al agente, este recorre el mismo camino, como en una receta:")]
    s += [fig("flujo_simple.png", 15.2, "Figura 1. El camino que sigue cada mensaje. Los cuadros naranjos son las salidas cuando algo no sale bien.", DIAG)]
    s += [steps([
        ("Entender el mensaje", "Lee lo que escribiste y decide de qué se trata: inicio de jornada, avería, urgencia VIP o entrega fallida."),
        ("Recordar casos parecidos", "Busca en su memoria si algo así ya ocurrió y cómo se resolvió."),
        ("Decidir qué hacer", "Aplica la acción que corresponde: marcar el camión averiado, subir la prioridad de un pedido, reprogramar una entrega."),
        ("Planificar las entregas", "Calcula quién lleva qué y en qué orden, sin pasarse del peso de los camiones."),
        ("Revisar el plan", "Comprueba que se cumplan los horarios y el turno. Si algo no cuadra, intenta corregirlo hasta tres veces."),
        ("Ejecutar y avisar", "Guarda el nuevo plan, genera las hojas de ruta, avisa a los clientes afectados y registra el caso."),
    ])]
    s += [P("Y si algo falla", "h2")]
    s += bullets(["Si falta un dato (por ejemplo, no dices qué camión), el agente <b>lo pregunta</b>.",
                  "Si no entiende el mensaje, <b>avisa a un supervisor</b> y no toca el plan.",
                  "Si después de corregir tres veces el plan sigue sin cumplirse, <b>avisa a un supervisor</b>."])

    s += [P("Un ejemplo real, paso a paso", "h2")]
    s += [P("Mensaje escrito: <b>«A las 11:00 el camión 3 se averió en la Zona Norte»</b>. Esto fue lo que hizo el agente "
            "(son las líneas reales que muestra el panel):")]
    s += [table([
        ["Lo que muestra el panel", "Qué significa"],
        ["Clasificado como avería · camión 3", "Entendió que se trata de una avería y de qué camión."],
        ["Memoria larga: incidente similar (similitud 0,72)", "Recordó una avería parecida de otro día y cómo se resolvió."],
        ["Reloj simulado a 11:00; entregas ya realizadas: 9", "Avanzó la hora y dio por entregados los pedidos que ya debían estar listos."],
        ["Camión 3 marcado como averiado", "Lo sacó del plan."],
        ["Plan calculado: 16 entregas en 4 camiones", "Repartió las 16 entregas pendientes entre los 4 camiones que quedan."],
        ["Validación: el plan cumple capacidad, ventanas y turnos", "Comprobó que nadie se pase de peso ni llegue fuera de horario."],
        ["Avisos redactados: 9", "Escribió un aviso a cada cliente cuyo pedido cambió de camión o de hora."],
        ["Incidente registrado y almacenado en memoria larga", "Guardó el caso para recordarlo en el futuro."],
    ], [6.6, W / cm - 6.6])]

    # ----------------------------------------------------------- 4
    s += [P("4. Las piezas del sistema", "h1")]
    s += [P("Por dentro, el sistema tiene varias partes que trabajan juntas. La figura 2 las muestra y la tabla explica cada una con "
            "una comparación.")]
    s += [fig("arquitectura_simple.png", 12.0, "Figura 2. Las piezas del sistema y cómo se conectan.", DIAG)]
    s += [table([
        ["Pieza", "Qué hace", "Se parece a…"],
        ["Panel web", "La pantalla donde escribes los mensajes y ves los resultados.", "El escritorio del despachador."],
        ["API", "Lleva los mensajes entre el panel y el agente.", "Un mensajero."],
        ["Agente", "Sigue el camino de pasos de la figura 1 y toma las decisiones.", "El cerebro."],
        ["Herramientas", "Funciones que consultan datos (flota, pedidos) o escriben (asignar, avisar).", "Las manos."],
        ["Planificador", "Reglas y cálculos que reparten los pedidos y revisan el plan.", "Una calculadora con reglas."],
        ["Modelo de lenguaje (IA)", "Entiende textos y redacta los avisos.", "Un asistente que sabe leer y escribir."],
        ["Memoria corta", "Guarda lo ocurrido en la jornada de hoy.", "El cuaderno del día."],
        ["Memoria larga", "Guarda casos pasados y los busca por su significado.", "Un archivador con casos."],
        ["Bases de datos", "Guardan flota, pedidos, clientes e incidentes (SQLite) y los casos buscables (ChromaDB).", "Las libretas de la empresa."],
    ], [3.4, 8.2, W / cm - 11.6])]

    # ----------------------------------------------------------- 5
    s += [PageBreak(), P("5. Recorrido por el panel", "h1")]
    s += [P("El panel se abre en el navegador, en la dirección <b>http://127.0.0.1:8000</b>. A la izquierda hay un menú con seis "
            "secciones. Esto es lo que hace cada una.")]
    s += [P("5.1 Centro de control", "h2")]
    s += [P("Es la pantalla principal: aquí escribes los mensajes y ves cómo reacciona el agente.", "lead")]
    s += [fig("dash_a.jpg", 16.4, "Figura 3. Centro de control (parte superior). Los números se explican abajo.")]
    s += [table([
        ["N°", "Qué es", "Para qué sirve"],
        ["1", "Indicadores del día", "Entregas pendientes, camiones operativos, cambios del día y avisos enviados."],
        ["2", "Consola de eventos", "Aquí escribes lo que ocurrió o pulsas un botón de <i>escenarios rápidos</i> y luego «Enviar al agente»."],
        ["3", "Razonamiento del agente", "Cada paso que dio el agente, en orden. Sirve para entender por qué decidió así."],
        ["7", "Menú", "Cambia entre las seis secciones del panel."],
        ["8", "Reloj y modo", "Hora simulada de la jornada y modo de IA en uso."],
    ], [1.2, 4.2, W / cm - 5.4])]
    s += [Spacer(1, 6)]
    s += [fig("dash_b.jpg", 15.2, "Figura 4. Centro de control (parte inferior).")]
    s += [table([
        ["N°", "Qué es", "Para qué sirve"],
        ["4", "Flota", "Estado de cada camión: disponible o averiado, carga, paradas pendientes y zona."],
        ["5", "Gráficos", "Kilos asignados a cada camión y estado de los 25 pedidos."],
        ["6", "Últimos avisos a clientes", "Los mensajes que el agente redactó (el envío es simulado)."],
    ], [1.2, 4.2, W / cm - 5.4])]

    s += [P("5.2 Rutas y flota", "h2")]
    s += [P("Muestra el recorrido de cada camión. Eliges un camión arriba y ves sus paradas en orden, con la <b>hora estimada de "
            "llegada</b> y si ya fue entregado.", "lead")]
    s += [fig("rutas.jpg", 14.4, "Figura 5. Ruta del camión 1: cinco entregas hechas y dos pendientes.")]
    s += bullets(["La franja oscura resume paradas pendientes, carga y hora en que terminaría.",
                  "El ícono de corona marca a los clientes VIP.",
                  "Un camión averiado aparece con una advertencia y sin entregas asignadas."])
    s += [P("5.3 Pedidos", "h2")]
    s += [P("Lista los 25 pedidos con su cliente, hora estimada, camión y estado. Puedes buscar por cliente, zona o número, y "
            "filtrar por estado. Al hacer clic en un pedido, a la derecha aparece su detalle.", "lead")]
    s += [fig("pedidos.jpg", 14.4, "Figura 6. Lista de pedidos con el detalle del pedido 14 (cliente VIP).")]
    s += bullets(["<b>Entregado</b>: ya se hizo. <b>Asignado</b>: tiene camión y hora. <b>Reprogramado</b>: pasa al día siguiente. "
                  "<b>Escalado</b>: lo revisa un supervisor.",
                  "En el detalle, <b>P4</b> significa prioridad máxima (urgente)."])

    s += [P("5.4 Memoria", "h2")]
    s += [P("Aquí se ve lo que el agente recuerda. Tiene tres pestañas.", "lead")]
    s += [P("Memoria corta: lo que pasó hoy", "h3")]
    s += [fig("memoria_corta.jpg", 13.2, "Figura 7. Eventos de la jornada y contador de cambios del plan.")]
    s += [P("Cuenta los cambios del día. Cuando llegan a tres, el agente avisa que la jornada está <b>inestable</b>.")]
    s += [P("Memoria larga: casos pasados", "h3")]
    s += [fig("memoria_larga.jpg", 13.2, "Figura 8. Incidentes registrados, con la estrategia que se usó en cada uno.")]
    s += [P("Cada caso nuevo se guarda aquí automáticamente y queda disponible para el futuro.")]

    s += [P("Búsqueda por significado", "h3")]
    s += [P("Permite probar cómo recuerda el agente. Escribes una frase con tus palabras y muestra los casos más parecidos, "
            "con un porcentaje de parecido. Aunque digas «se me rompió una rueda», encuentra averías que no usan esas palabras.", "lead")]
    s += [fig("memoria_busqueda.jpg", 14.2, "Figura 9. Búsqueda «se me rompió una rueda del camión»: las averías pasadas aparecen primero.")]
    s += [callout("¿Qué significa el porcentaje?", "Es qué tan parecido es el mensaje a un caso guardado. El agente solo usa un caso si "
                                                   "supera el <b>60 %</b>; así evita confundirse con casos que no tienen relación.")]

    s += [P("5.5 Asistente", "h2")]
    s += [P("Es un chat para hacer preguntas sobre la operación: «¿qué camiones están disponibles?», «¿cuál es la ruta del "
            "camión 2?». Aquí la IA decide por sí sola qué herramienta de consulta usar. <b>Solo consulta: no cambia el plan</b>. "
            "Necesita un modelo de IA (Ollama o Groq); en modo «Reglas» el panel te lo indica y ofrece cambiar.", "lead")]
    s += [fig("asistente.jpg", 14.4, "Figura 10. Asistente en modo «Reglas»: pide activar un modelo de IA para conversar.")]
    s += [P("5.6 Ajustes", "h2")]
    s += [P("Permite elegir el modo de IA (<b>Reglas</b>, <b>Ollama</b> o <b>Groq</b>), reiniciar la jornada y ver el estado del sistema.", "lead")]
    s += [fig("ajustes.jpg", 14.4, "Figura 11. Ajustes: modo de IA, botón para reiniciar la jornada y estado del sistema.")]

    s += [P("5.7 También funciona en el celular", "h2")]
    with PILImage.open(PROC / "movil.jpg") as _im:
        _w, _h = _im.size
    phone = [Image(str(PROC / "movil.jpg"), width=4.6 * cm, height=4.6 * cm * _h / _w), Spacer(1, 3),
             P("Figura 12. Vista para celular.", "cap")]
    txt = [P("En pantallas pequeñas el menú pasa a una <b>barra flotante</b> abajo y el contenido se ordena en una sola columna, "
             "para poder usar el panel desde el teléfono o la tableta."),
           P("Todo lo que se explicó antes funciona igual: escribir mensajes, ver el razonamiento del agente, revisar camiones, "
             "pedidos y memoria.")]
    two = Table([[phone, txt]], colWidths=[5.4 * cm, W - 5.4 * cm])
    two.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    s += [KeepTogether([two])]

    # ----------------------------------------------------------- 6
    s += [P("6. Cómo probarlo: seis pasos", "h1")]
    s += [P("Con el sistema encendido, abre el <b>Centro de control</b> y pulsa los botones de <i>escenarios rápidos</i> en este "
            "orden. Después de cada uno, mira el panel «Razonamiento del agente».")]
    s += [table([
        ["Paso", "Qué haces", "Qué deberías ver"],
        ["1", "Pulsa <b>Inicio de jornada</b>.", "25 pedidos repartidos entre los 5 camiones y 25 avisos a clientes."],
        ["2", "Pulsa <b>Avería camión 3</b>.", "El camión 3 queda en rojo, sus entregas pasan a otros camiones y se avisa a los afectados."],
        ["3", "Pulsa <b>VIP urgente</b>.", "El pedido 14 sube a prioridad máxima y llega antes de la hora límite."],
        ["4", "Pulsa <b>Entrega fallida</b> y luego <b>Segundo fallo</b>.", "Primero se reprograma el pedido; al segundo fallo pasa a un supervisor."],
        ["5", "Pulsa <b>Evento ambiguo</b>.", "El agente no inventa nada: pide el dato que falta o avisa a un supervisor."],
        ["6", "Abre <b>Memoria</b> y prueba la búsqueda.", "Verás los eventos del día y los casos pasados que el agente recuerda."],
    ], [1.4, 6.0, W / cm - 7.4])]
    s += [Spacer(1, 8), P("También puedes escribir tus propios mensajes en la consola. Por ejemplo:")]
    s += bullets(["<i>A las 15:00 el camión 2 se averió</i>", "<i>El cliente 5 (VIP) necesita su pedido 3 antes de las 12:00</i>",
                  "<i>Cliente ausente en el pedido 11</i>"])
    s += [callout("Para volver a empezar", "En <b>Ajustes</b> pulsa «Reiniciar jornada» (o el ícono de flecha circular arriba a la derecha). "
                                           "Se regeneran los datos y el agente empieza de cero.")]

    # ----------------------------------------------------------- 7
    s += [PageBreak(), P("7. Ideas clave explicadas simple", "h1")]
    s += [P("Memoria corta y memoria larga", "h2")]
    s += [table([
        ["", "Memoria corta", "Memoria larga"],
        ["¿Qué guarda?", "Lo que ocurrió en el día de hoy.", "Casos de otros días y cómo se resolvieron."],
        ["¿Cómo se parece a lo humano?", "Al cuaderno donde anotas el día.", "Al archivador con casos antiguos."],
        ["¿Cómo busca?", "No busca: sigue disponible.", "Por significado, no por palabras exactas."],
        ["¿Para qué la usa?", "Contar cambios del día y no olvidar lo ya hecho.", "Sugerir qué hacer según casos parecidos."],
        ["¿Qué pasa si se reinicia?", "Se conserva.", "Se conserva."],
    ], [4.0, 6.4, W / cm - 10.4])]
    s += [P("Cómo decide qué pedido va primero", "h2")]
    s += [P("A cada pedido se le calcula un <b>puntaje de urgencia</b>. Sube si:")]
    s += bullets(["el cliente es <b>VIP</b>;", "el pedido tiene <b>prioridad alta</b>;", "queda <b>poco tiempo</b> antes de que cierre su ventana de horas."])
    s += [P("Luego se reparten entre los camiones según el <b>peso</b> que puede llevar cada uno y la <b>cercanía</b> entre zonas, "
            "y se ordenan para cumplir los horarios. Un camión <b>nunca</b> recibe más peso del que soporta.")]
    s += [P("Qué hace la IA y qué hacen las reglas", "h2")]
    s += [table([
        ["Lo hace la IA (modelo de lenguaje)", "Lo hacen las reglas (programa tradicional)"],
        ["Entender el mensaje escrito con palabras normales.", "Decidir qué pedido va primero y qué camión lo lleva."],
        ["Redactar los avisos a los clientes.", "Comprobar peso, horarios y turnos."],
        ["Conversar en el Asistente.", "Verificar que los camiones y pedidos mencionados existen."],
    ], [W / cm / 2, W / cm / 2])]
    s += [Spacer(1, 6), callout("¿Por qué no dejar todo a la IA?",
                                "Durante las pruebas, el modelo pequeño que funciona en el computador leyó «<i>cliente ausente en el "
                                "pedido 8</i>» y entendió «<i>inicio de jornada</i>»: habría rehecho todo el plan del día. Por eso las "
                                "decisiones importantes las toman reglas claras que se pueden comprobar, y la IA solo ayuda a "
                                "entender y escribir. Cada medida de seguridad tiene una prueba automática.", YELLOW_SOFT, YELLOW)]
    s += [P("Los tres modos de IA", "h2")]
    s += [table([
        ["Modo", "Qué es", "Cuándo usarlo"],
        ["Reglas", "Sin IA: clasifica con reglas y escribe avisos con plantillas.", "Demostraciones rápidas o sin internet. Es el más rápido."],
        ["Ollama", "IA que corre en el propio computador (modelo pequeño, gratis).", "Mostrar la IA real sin internet. Tarda unos 20 segundos por mensaje."],
        ["Groq", "IA en la nube con un modelo grande (gratis con límites).", "Mejores respuestas. Requiere internet y una clave en el archivo .env."],
    ], [2.4, 7.0, W / cm - 9.4])]
    s += [P("Cuándo el agente pide ayuda a un supervisor", "h2")]
    s += bullets(["No entiende el mensaje.", "Una entrega falla por segunda vez.",
                  "Después de tres intentos de corrección, el plan sigue sin cumplir los horarios.",
                  "Ya no quedan camiones disponibles.", "En la jornada hubo tres o más cambios seguidos (jornada inestable)."])

    # ----------------------------------------------------------- 8
    s += [PageBreak(), P("8. Cómo encender el sistema", "h1")]
    s += [P("Requisitos", "h2")]
    s += bullets(["Python instalado (ya está en este computador).",
                  "Ollama instalado, con los modelos <i>nomic-embed-text</i> (memoria) y <i>qwen2.5:1.5b</i> (IA local).",
                  "Un navegador (Edge o Chrome)."])
    s += [P("Encender", "h2")]
    s += [P("Abre una terminal (PowerShell) en la carpeta <b>cordillera-dispatch-agent</b> y escribe:")]
    s += [codebox([".\\.venv\\Scripts\\python.exe -m uvicorn api.main:app --port 8000"])]
    s += [P("Cuando diga <i>Application startup complete</i>, abre en el navegador <b>http://127.0.0.1:8000</b>. "
            "Cada vez que se enciende, el sistema comienza una jornada limpia.")]
    s += [P("Apagar", "h2")]
    s += [P("En la terminal donde está corriendo, presiona <b>Ctrl + C</b>.")]
    s += [P("Probar que todo funciona", "h2")]
    s += [codebox([".\\.venv\\Scripts\\python.exe -m pytest"])]
    s += [P("Debe mostrar <b>57 passed</b>: son las 57 pruebas automáticas, que se ejecutan sin internet y sin IA.")]
    s += [P("Si algo no funciona", "h2")]
    s += [table([
        ["Qué ves", "Qué hacer"],
        ["El navegador no abre el panel.", "Revisa que la terminal siga corriendo el servidor. Si no, vuelve a ejecutar el comando de encendido."],
        ["Cada mensaje tarda mucho.", "Entra a Ajustes y cambia a modo <b>Reglas</b>, que responde al instante."],
        ["Aparece «Modo degradado».", "Ollama no está activo. Ábrelo y reinicia el servidor para recuperar la búsqueda por significado completa."],
        ["El Asistente dice que necesita un LLM.", "Cambia el modo a Ollama (o Groq) en Ajustes."],
        ["Quieres empezar de cero.", "Pulsa «Reiniciar jornada» en Ajustes."],
    ], [5.2, W / cm - 5.2])]
    s += [P("Dónde está cada cosa", "h2")]
    s += [table([
        ["Carpeta o archivo", "Qué contiene"],
        ["src/", "El cerebro del agente: flujo, planificador, memoria y herramientas."],
        ["api/", "El servicio que conecta el panel con el agente."],
        ["frontend/", "El panel web (lo que ves en pantalla)."],
        ["data/", "Datos inventados, políticas de la empresa y el generador de datos."],
        ["tests/", "Las 57 pruebas automáticas."],
        ["docs/", "Diagramas, bocetos, evidencia de pruebas, informe, presentación y esta guía."],
        ["README.md", "Instrucciones técnicas resumidas para quien revise el proyecto."],
    ], [4.2, W / cm - 4.2])]

    # ----------------------------------------------------------- 9
    s += [PageBreak(), P("9. Preguntas frecuentes", "h1")]
    faq = [
        ("¿Es un sistema real?", "No. Es un ejercicio académico con datos inventados, pero funciona de principio a fin y está probado."),
        ("¿Envía correos o mensajes reales?", "No. Los avisos se redactan y se guardan en un archivo (envío simulado)."),
        ("¿Qué pasa si la IA se equivoca?", "Las reglas tienen prioridad, se verifica que lo mencionado exista y los avisos se revisan antes de usarse. Además, hay pruebas para estos casos."),
        ("¿Funciona sin internet?", "Sí, en modo Reglas o con Ollama. Solo Groq necesita internet."),
        ("¿Cuánto cuesta?", "Nada. Todo el software usado es gratuito."),
        ("¿Puedo cambiar los datos?", "Sí. Los datos salen de data/seed.py; allí se pueden cambiar camiones, clientes y pedidos."),
        ("¿Cómo sé que funciona?", "Con las 57 pruebas automáticas y los 9 escenarios cuyo paso a paso está en docs/evidencia."),
        ("¿Por qué recuerda casos si no los escribí yo?", "Porque al empezar carga 15 casos de ejemplo, y además guarda cada caso nuevo que ocurre."),
    ]
    for q, a in faq:
        s += [KeepTogether([P(q, "h3"), P(a)])]
    s += [P("Glosario", "h2")]
    s += [table([
        ["Palabra", "Significado"],
        ["Agente", "Programa con IA que decide y actúa usando herramientas."],
        ["API", "Conexión que permite que el panel hable con el agente."],
        ["Despacho", "Repartir los pedidos entre los camiones y ordenar las entregas."],
        ["ETA", "Hora estimada de llegada de un pedido."],
        ["Escalar", "Pasar un caso a una persona (el supervisor)."],
        ["Jornada", "El día de trabajo, de 08:00 a 18:00."],
        ["LangGraph", "Biblioteca que organiza los pasos del agente como un mapa con decisiones."],
        ["Modelo de lenguaje (LLM)", "IA que entiende y escribe texto. Aquí: Llama 3.3 (Groq) y Qwen2.5 (Ollama)."],
        ["Prioridad", "Número del 1 al 4 que indica qué tan urgente es un pedido (4 es máxima)."],
        ["Ventana horaria", "Rango de horas en que el cliente puede recibir su pedido."],
        ["VIP", "Cliente con servicio prioritario."],
    ], [4.4, W / cm - 4.4])]

    # un título nunca queda solo al final de una página: se une al bloque que le sigue
    out, i = [], 0
    while i < len(s):
        el = s[i]
        if isinstance(el, Paragraph) and el.style.name in ("h1", "h2", "h3") and i + 1 < len(s) and isinstance(s[i + 1], KeepTogether):
            out.append(KeepTogether([el] + list(s[i + 1]._content)))
            i += 2
        else:
            out.append(el)
            i += 1
    return out


def build():
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2.0 * cm, bottomMargin=1.8 * cm,
                          title="Guía simple del sistema · Agente de despacho y rutas", author="Equipo del proyecto",
                          subject="Explicación en lenguaje simple del sistema")
    frame = Frame(2 * cm, 1.8 * cm, W, A4[1] - 3.8 * cm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=cover, autoNextPageTemplate="body"),
                          PageTemplate(id="body", frames=[frame], onPage=on_page)])
    doc.build(story())
    return OUT


if __name__ == "__main__":
    print("Guía generada:", build())
