"""Genera el informe del proyecto sobre la plantilla institucional del Duoc UC.

Conserva el paquete de la plantilla (estilos, encabezado con logo, pie de página, numeración)
y reemplaza el cuerpo del documento. Uso:

    python scripts/build_informe_duoc.py --template "<ruta a la plantilla .docx>" [--toc 3,3,3,...]

El índice se rellena con los números de página que se le pasan en --toc (JSON con
{"bookmark": página}); si no se pasan, usa 0 y se recalcula en una segunda pasada.
"""
import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "informe" / "Informe_EP2_ISY0101_Duoc.docx"

# ------------------------------------------------------------------ datos del informe
DOC_NAME = "Agente de despacho y rutas"
SUBTITLE = "Transportes Cordillera (caso de estudio)"
COURSE = "ISY0101 Ingeniería de Soluciones con IA"
TEAM = "Duoc UC · Evaluación Parcial N°2"
COURSE_CODE = "ISY0101 · Ingeniería de Soluciones con IA"
DATE_COVER = "Octubre 22, 2026"
DATE_SHORT = "22/10/2026"
MEMBERS = ["Fabián Armijo", "[Nombre del segundo integrante]"]
BODY_SZ = 21        # 10,5 pt
TABLE_SZ = 18       # 9,5 pt

W = 9029            # ancho útil en twips (A4, márgenes de la plantilla)
NS_REQUIRED = ("xmlns:wp=", "xmlns:a=", "xmlns:pic=", "xmlns:r=")


# ------------------------------------------------------------------ utilidades XML
def esc(t: str) -> str:
    return escape(t)


def run(text, b=False, i=False, color=None, sz=None, font=None):
    pr = ""
    if font:
        pr += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'
    if b:
        pr += '<w:b w:val="1"/><w:bCs w:val="1"/>'
    if i:
        pr += '<w:i w:val="1"/><w:iCs w:val="1"/>'
    if color:
        pr += f'<w:color w:val="{color}"/>'
    if sz:
        pr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    return f'<w:r><w:rPr>{pr}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def rich(text, sz=BODY_SZ, color=None):
    """Texto con **negritas** y _cursivas_ simples."""
    out = []
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if part.startswith("**") and part.endswith("**"):
            out.append(run(part[2:-2], b=True, sz=sz, color=color))
        elif part:
            out.append(run(part, sz=sz, color=color))
    return "".join(out)


def para(content, jc=None, style=None, before=None, after=None, ind=None, keep_next=False, line=None, extra=""):
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        ppr += '<w:keepNext w:val="1"/>'
    ppr += extra
    sp = ""
    if before is not None:
        sp += f' w:before="{before}"'
    if after is not None:
        sp += f' w:after="{after}"'
    if line is not None:
        sp += f' w:line="{line}" w:lineRule="auto"'
    if sp:
        ppr += f"<w:spacing{sp}/>"
    if ind:
        ppr += f"<w:ind {ind}/>"
    if jc:
        ppr += f'<w:jc w:val="{jc}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{content}</w:p>"


def body_p(text, after=90, jc="both"):
    return para(rich(text), after=after, jc=jc)


BOOKMARKS: list[tuple[int, str, str]] = []  # (nivel, texto, nombre)


def heading(level, text):
    name = f"_toc{len(BOOKMARKS) + 1:03d}"
    BOOKMARKS.append((level, text, name))
    bid = len(BOOKMARKS) + 100
    inner = f'<w:bookmarkStart w:id="{bid}" w:name="{name}"/>{run(text)}<w:bookmarkEnd w:id="{bid}"/>'
    if level == 1:
        return para(inner, style="Heading1", extra='<w:pageBreakBefore w:val="0"/>', before=170, after=70)
    return para(inner, style="Heading2", ind='w:left="0" w:firstLine="0"', before=120, after=50)


def bullet(text, sz=BODY_SZ):
    return (f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="3"/></w:numPr>'
            f'<w:spacing w:after="60"/><w:ind w:left="720" w:hanging="360"/></w:pPr>{rich(text, sz)}</w:p>')


def page_break():
    return '<w:p><w:pPr><w:spacing w:after="0"/></w:pPr><w:r><w:br w:type="page"/></w:r></w:p>'


def empty(after=0):
    return (f'<w:p><w:pPr><w:spacing w:after="{after}" w:line="240" w:lineRule="auto"/>'
            f'<w:rPr><w:sz w:val="8"/><w:szCs w:val="8"/></w:rPr></w:pPr></w:p>')


def cell(content_xml, width, fill=None, valign="top"):
    shd = f'<w:shd w:fill="{fill}" w:val="clear"/>' if fill else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shd}'
            f'<w:tcMar><w:top w:w="70" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
            f'<w:bottom w:w="70" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tcMar>'
            f'<w:vAlign w:val="{valign}"/></w:tcPr>{content_xml}</w:tc>')


def cell_p(text, sz=TABLE_SZ, b=False, jc="left", color=None, keep=False):
    content = run(text, b=True, sz=sz, color=color) if b else rich(text, sz, color)
    return para(content, jc=jc, after=0, line=240, keep_next=keep)


def table(widths, rows, header=True, sz=TABLE_SZ, centered_cols=(), keep_all=False):
    assert sum(widths) == W, sum(widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    border = ('<w:tblBorders>' + "".join(
        f'<w:{s} w:color="000000" w:space="0" w:sz="8" w:val="single"/>'
        for s in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>")
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{W}" w:type="dxa"/><w:jc w:val="left"/>{border}'
           f'<w:tblLayout w:type="fixed"/><w:tblLook w:val="0600"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    for r, row in enumerate(rows):
        is_head = header and r == 0
        trpr = '<w:trPr><w:cantSplit w:val="1"/>' + ('<w:tblHeader w:val="1"/>' if is_head else "") + "</w:trPr>"
        cells = []
        for c, txt in enumerate(row):
            jc = "center" if (is_head or c in centered_cols) else "left"
            fill = "d9d9d9" if is_head else None
            cells.append(cell(cell_p(txt, sz, b=is_head, jc=jc, keep=(r < len(rows) - 1) if keep_all else (r < min(2, len(rows) - 1))), widths[c], fill))
        out.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out) + empty(40)


def kv_table(rows, label_w=4514, sz=BODY_SZ):
    """Tabla de dos columnas de la plantilla (columna izquierda gris y en negrita)."""
    widths = [label_w, W - label_w]
    border = ('<w:tblBorders>' + "".join(
        f'<w:{s} w:color="000000" w:space="0" w:sz="8" w:val="single"/>'
        for s in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>")
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{W}" w:type="dxa"/><w:jc w:val="left"/>{border}'
           f'<w:tblLayout w:type="fixed"/><w:tblLook w:val="0600"/></w:tblPr>'
           f'<w:tblGrid><w:gridCol w:w="{widths[0]}"/><w:gridCol w:w="{widths[1]}"/></w:tblGrid>']
    for k, v in rows:
        out.append('<w:tr><w:trPr><w:cantSplit w:val="1"/></w:trPr>'
                   + cell(cell_p(k, sz, b=True), widths[0], "d9d9d9")
                   + cell(cell_p(v, sz), widths[1]) + "</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


_IMG_ID = [10]


SIZES: dict[str, tuple[int, int]] = {}


def image(rid, w_cm, key, descr):
    pw, ph = SIZES[key]
    h_cm = w_cm * ph / pw
    cx, cy = int(w_cm * 360000), int(h_cm * 360000)
    _IMG_ID[0] += 1
    n = _IMG_ID[0]
    drawing = (
        f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{n}" name="Imagen {n}" descr="{esc(descr)}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{n}" name="Imagen {n}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
        f'</wp:inline></w:drawing>')
    return para(f"<w:r>{drawing}</w:r>", jc="center", before=60, after=40, keep_next=True)


def caption(text):
    return para(run(text, i=True, sz=18, color="666666"), jc="center", after=140)


# ------------------------------------------------------------------ cuerpo
def build_body(toc_pages: dict[str, int], image_rids: dict[str, str]) -> str:
    BOOKMARKS.clear()
    parts: list[str] = []
    add = parts.append

    # ---------- portada (misma disposición que la plantilla)
    for _ in range(6):
        add('<w:p><w:pPr><w:pStyle w:val="Title"/><w:pageBreakBefore w:val="0"/></w:pPr></w:p>')
    add(para(run(DOC_NAME), style="Title", jc="center"))
    add(para(run(SUBTITLE, sz=40), style="Subtitle"))
    for _ in range(9):
        add(empty())
    add(para(run(COURSE_CODE, b=True), jc="right"))
    add(empty())
    add(para(run(DATE_COVER, b=True, color="666666"), jc="right"))
    add(empty())
    for m in MEMBERS:
        add(para(run(m, color="666666"), jc="right"))
    add(page_break())

    # ---------- información del proyecto
    add(para(run("Información del proyecto", b=True, sz=34), after=120))
    add(kv_table([
        ("Empresa / Organización", "Transportes Cordillera (empresa ficticia usada como caso de estudio)"),
        ("Proyecto", "Agente de despacho y rutas con inteligencia artificial"),
        ("Fecha de preparación", DATE_SHORT),
        ("Cliente", "Duoc UC · Asignatura ISY0101 Ingeniería de Soluciones con IA"),
        ("Patrocinador principal", "Docente de la asignatura: [Nombre del docente]"),
        ("Gerente / Líder de Proyecto", MEMBERS[0]),
        ("Gerente / Líder de Análisis de negocio y requerimientos", MEMBERS[1]),
    ]))
    add(empty(160))
    add(para(run("Historial de revisiones", b=True, sz=34), after=120, keep_next=True))
    add(table([1300, 1000, 3629, 1500, 1600],
              [["Fecha", "Versión", "Descripción", "Organización", "Autor"],
               [DATE_SHORT, "1.0", "Primera versión del informe de la Evaluación Parcial N°2", "Duoc UC", "Equipo del proyecto"]],
              sz=20, centered_cols=(0, 1)))
    add(empty(100))
    add(para(run("Aprobaciones", b=True, sz=34), after=120, keep_next=True))
    add(table([2300, 1700, 2029, 1500, 1500],
              [["Nombre y apellido", "Cargo", "Departamento u organización", "Fecha", "Firma"],
               [MEMBERS[0], "Líder de proyecto", "Duoc UC", "", ""],
               [MEMBERS[1], "Integrante", "Duoc UC", "", ""],
               ["[Nombre del docente]", "Docente", "Duoc UC", "", ""]], sz=20))
    add(page_break())

    # ---------- contenidos (se completa al final, cuando se conocen los encabezados)
    add("@@TOC@@")
    add(page_break())

    # ---------- Introducción
    add(heading(1, "Introducción"))
    add(body_p("Este informe presenta un agente de inteligencia artificial (IA) que ayuda a organizar el reparto "
               "diario de una empresa de transporte ficticia llamada Transportes Cordillera. El agente recibe avisos "
               "escritos con palabras normales, como «el camión 3 se averió», y decide qué hacer: ordena de nuevo "
               "las entregas, avisa a los clientes y guarda lo ocurrido para recordarlo después."))
    add(heading(2, "Alcance"))
    add(body_p("El proyecto entrega un agente que funciona de principio a fin con datos inventados: 5 camiones, "
               "25 pedidos del día y 10 clientes. Resuelve tres situaciones: la avería de un camión, un cliente VIP "
               "que pide urgencia y una entrega que falla. Los avisos a los clientes se simulan y quedan guardados en un archivo."))
    add(heading(2, "Propósito"))
    add(body_p("Mostrar que un agente puede apoyar el trabajo de una organización: usa herramientas de consulta y de "
               "escritura, razona sobre lo que ocurre, recuerda casos anteriores y cambia su plan cuando las "
               "condiciones cambian. Además, el trabajo queda documentado para que otra persona pueda ejecutarlo y comprobarlo."))
    add(heading(2, "Ámbito"))
    add(body_p("Corresponde a la Evaluación Parcial N°2 de la asignatura Ingeniería de Soluciones con IA (ISY0101), "
               "desarrollada en parejas y solo con herramientas gratuitas. Es un ejercicio académico: antes de "
               "usarlo en una empresa real habría que probarlo con datos reales."))
    add(heading(2, "Descripción"))
    add(body_p("Una persona escribe lo que ocurrió. El agente entiende el mensaje, busca casos parecidos en su memoria, "
               "cambia lo necesario en el plan y revisa que sea posible (peso de los camiones, horarios de los "
               "clientes y turno de trabajo). Luego avisa a los clientes afectados y registra el caso. Si no entiende "
               "el mensaje, pide el dato que falta o avisa a un supervisor. La decisión importante, como qué pedido "
               "va primero, la toma un programa con reglas claras y verificables; el modelo de lenguaje (la IA que "
               "entiende textos) solo interpreta mensajes y redacta avisos."))
    add(heading(2, "Definiciones, acrónimos y abreviaciones"))
    add(table([2300, 6729], [
        ["Término", "Significado"],
        ["Agente", "Programa con IA que decide y actúa usando herramientas."],
        ["Modelo de lenguaje", "IA que entiende y escribe texto. Aquí se usan Llama 3.3 (Groq) y Qwen2.5 (Ollama)."],
        ["LangGraph", "Biblioteca que organiza los pasos del agente como un mapa con decisiones."],
        ["Memoria corta y larga", "La corta guarda la jornada actual; la larga guarda casos pasados y los busca por significado."],
        ["VIP / API / escalar", "Cliente prioritario / conexión entre el panel web y el agente / pasar un caso al supervisor."],
    ]))
    add(heading(2, "Referencias"))
    refs = [
        "Chase, H. (2022). LangChain [Software]. GitHub. https://github.com/langchain-ai/langchain",
        "Chroma. (2023). Chroma: The AI-native open-source embedding database. https://www.trychroma.com/",
        "Groq, Inc. (2024). GroqCloud documentation. https://console.groq.com/docs",
        "LangChain, Inc. (2024). LangGraph documentation. https://langchain-ai.github.io/langgraph/",
        "Nussbaum, Z., Morris, J. X., Duderstadt, B., & Mulyar, A. (2024). Nomic Embed: Training a reproducible long "
        "context text embedder. arXiv. https://arxiv.org/abs/2402.01613",
        "Ollama. (2023). Ollama [Software]. https://ollama.com",
        "Qwen Team. (2024). Qwen2.5 technical report. arXiv. https://arxiv.org/abs/2412.15115",
        "Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing "
        "reasoning and acting in language models. International Conference on Learning Representations. "
        "https://arxiv.org/abs/2210.03629",
    ]
    for r in refs:
        add(para(run(r, sz=18), after=30, ind='w:left="567" w:hanging="567"', jc="left", line=240))

    # ---------- Desarrollo
    add(heading(1, "Desarrollo y explicación detallada"))
    add(heading(2, "Requerimientos"))
    add(table([3000, 6029], [
        ["Requerimiento", "Cómo se cumple"],
        ["Herramientas de consulta, escritura y razonamiento", "Más de veinte herramientas: leen flota y pedidos, asignan entregas, escriben hojas de ruta y avisos, y clasifican mensajes."],
        ["Recordar lo ocurrido", "Memoria corta de la jornada y memoria larga con casos pasados."],
        ["Adaptarse a los cambios", "Reorganiza el plan ante una avería, un cliente VIP urgente o una entrega fallida."],
        ["Pedir ayuda y costo cero", "Pide datos o avisa a un supervisor si no hay solución. Usa Groq (gratis), Ollama o un modo sin IA."],
    ]))
    add(heading(2, "Metodología"))
    add(body_p("El trabajo se hizo en cinco pasos, probando cada parte antes de seguir: **(1)** definir el caso con "
               "empresa, flota, clientes y pedidos inventados; **(2)** programar las reglas del planificador y las "
               "herramientas que leen y escriben datos; **(3)** armar el agente con LangGraph y agregar las dos "
               "memorias; **(4)** probar con 9 escenarios y 57 pruebas, corrigiendo los errores encontrados; y "
               "**(5)** construir el panel web y documentar con README, diagramas e informe."))
    add(heading(2, "Modelos"))
    add(body_p("**Planificación.** Cada pedido recibe un puntaje de urgencia: sube si el cliente es VIP, si el pedido tiene "
               "prioridad alta o si le queda poco tiempo en su ventana horaria. Se reparten según el peso que carga "
               "cada camión y la cercanía de las zonas, y luego se ordenan para cumplir los horarios."))
    add(table([2500, 6529], [
        ["Situación", "Qué hace el agente"],
        ["Avería de un camión", "Lo saca del plan, reparte sus entregas pendientes entre los otros camiones y avisa a los clientes afectados."],
        ["Cliente VIP urgente", "Sube el pedido a la prioridad máxima, respeta la hora límite y reordena la ruta."],
        ["Entrega fallida", "La primera vez reintenta el mismo día (o mañana, si el cliente tiene ausencias previas); la segunda vez pasa el caso a un supervisor."],
        ["Mensaje confuso", "Pide el dato que falta o avisa al supervisor. No inventa información."],
    ], keep_all=True))
    add(body_p("**Memoria.** La corta guarda lo ocurrido en la jornada y sobrevive a un reinicio; con tres cambios en el "
               "día, el agente avisa que la jornada está inestable. La larga busca casos pasados por significado: al "
               "escribir «se me rompió una rueda» encuentra averías con 67 % de similitud (se aceptan sobre 60 %)."))
    add(body_p("**Arquitectura y flujo.** La persona usa un panel web, que habla con una API; la API entrega el mensaje al "
               "agente (figura 1). El agente sigue el flujo de la figura 2, con decisiones en cada paso: si el mensaje "
               "no se entiende, avisa a un supervisor; si falta un dato, lo pregunta; y si el plan no cumple las reglas, "
               "intenta corregirlo hasta tres veces antes de pedir ayuda."))
    add(image(image_rids["arq"], 10.6, "arq", "Diagrama de arquitectura de componentes del agente"))
    add(caption("Figura 1. Componentes del sistema: panel web, agente, herramientas, datos y modelo de lenguaje."))
    add(image(image_rids["flujo"], 14.8, "flujo", "Diagrama del flujo del agente con sus decisiones"))
    add(caption("Figura 2. Flujo del agente: entender, recordar, decidir, revisar el plan, ejecutar y avisar."))
    add(heading(2, "Pruebas y resultados"))
    add(body_p("Se hicieron 57 pruebas automáticas (sin internet y sin IA) y 9 escenarios que registran paso a paso lo "
               "que piensa el agente. Todas las pruebas pasan."))
    add(table([2500, 6529], [
        ["Escenario", "Resultado comprobado"],
        ["Avería a las 11:00", "9 entregas ya realizadas; 16 pendientes reasignadas; ningún pedido queda en el camión averiado."],
        ["Cliente VIP urgente", "El pedido 14 sube a prioridad 4 y se entrega a las 12:00, dentro de su hora límite."],
        ["Entrega fallida", "Primer fallo: reintento el mismo día. Segundo fallo: el pedido pasa a un supervisor."],
        ["Memoria larga", "Recuerda el caso de la batería (similitud 0,79) y la solución que se aplicó."],
        ["Otros casos", "Con tres cambios seguidos avisa de inestabilidad; sin IA sigue funcionando con reglas; ante mensajes confusos pide datos."],
    ]))
    add(body_p("**Hallazgo importante.** El modelo pequeño se equivocó al clasificar algunos mensajes. Por eso las reglas "
               "claras tienen prioridad, se comprueba que los camiones y pedidos mencionados existan, y los avisos que "
               "escribe la IA se revisan antes de enviarse. Cada caso quedó cubierto por una prueba automática. Los "
               "datos que respaldan cada decisión de diseño están en el archivo docs/decisiones.md del repositorio."))

    # ---------- Riesgos
    add(heading(1, "Riesgos"))
    add(table([2400, 3200, 3429], [
        ["Riesgo", "Qué podría pasar", "Cómo se controla"],
        ["El modelo de IA se equivoca", "Entiende mal un mensaje y cambia el plan.", "Las reglas tienen prioridad y hay pruebas para estos casos."],
        ["Falla el servicio gratuito o internet", "No se puede usar Groq en la demostración.", "Modo local con Ollama, modo sin IA y video de respaldo."],
        ["Poca memoria en el computador", "Los modelos grandes no funcionan.", "Se usan modelos pequeños; las decisiones críticas las toman reglas."],
    ]))

    # ---------- Hitos
    add(heading(1, "Hitos"))
    add(table([6029, 3000], [
        ["Hito", "Estado"],
        ["Agente, herramientas, memoria, panel web, pruebas y evidencia", "Completado"],
        ["Presentación con demostración en vivo", "Semana 12"],
        ["Entrega del informe y del repositorio", "Semana 13"],
    ], centered_cols=(1,), keep_all=True))

    # ---------- Entregables
    add(heading(1, "Entregables"))
    add(body_p("**Informe técnico** (este documento); **repositorio** con código, README, diagramas, bocetos y evidencia "
               "(enlace: [pegar enlace del repositorio]); y **presentación** de 20 minutos (10 de exposición y 10 de "
               "preguntas) con demostración en vivo."))

    # ---------- Conclusiones
    add(heading(1, "Conclusiones y reflexiones individuales"))
    add(body_p("**Resultados del proyecto:** el agente completa el flujo en los 9 escenarios, cambia su plan ante "
               "averías, urgencias y entregas fallidas, y las 57 pruebas pasan con herramientas gratuitas.", after=80))
    add(body_p("**Conclusiones del equipo:** [Escribir aquí, con sus propias palabras.]", after=80))
    add(body_p(f"**Reflexión de {MEMBERS[0]}:** [Escribir aquí el aprendizaje y el aporte personal.]", after=80))
    add(body_p(f"**Reflexión de {MEMBERS[1]}:** [Escribir aquí el aprendizaje y el aporte personal.]"))

    # ---------- IA
    add(heading(1, "Declaración de uso de inteligencia artificial"))
    add(body_p("Se usó Claude Code (modelo Claude Sonnet 5.5, de Anthropic) como apoyo para generar el código base, las "
               "pruebas, los diagramas, el panel web y los borradores de la documentación, de este informe y de la "
               "presentación. El equipo ejecutó, revisó y validó todo el contenido. Dentro del sistema, un modelo de "
               "lenguaje (Llama 3.3 en Groq o Qwen2.5 en Ollama) clasifica mensajes y redacta avisos, y sus respuestas "
               "se validan con reglas. Las conclusiones y las reflexiones individuales fueron redactadas por los "
               "integrantes sin apoyo de IA."))

    # ---------- Anexos
    add(heading(1, "Anexos"))
    add(para(run("Anexo A. Cómo ejecutar el sistema", b=True, sz=BODY_SZ), after=60, keep_next=True))
    code = ["pip install -r requirements.txt", "ollama pull nomic-embed-text", "copy .env.example .env",
            "python -m uvicorn api.main:app --port 8000", "pytest"]
    code_p = "".join(para(run(c, sz=18, font="Consolas"), after=10, jc="left", line=240) for c in code)
    add(f'<w:tbl><w:tblPr><w:tblW w:w="{W}" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblBorders>'
        + "".join(f'<w:{s} w:color="BFBFBF" w:space="0" w:sz="6" w:val="single"/>' for s in ("top", "left", "bottom", "right"))
        + f'</w:tblBorders></w:tblPr><w:tblGrid><w:gridCol w:w="{W}"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:tcW w:w="{W}" w:type="dxa"/>'
          f'<w:shd w:fill="F2F2F2" w:val="clear"/><w:tcMar><w:top w:w="70" w:type="dxa"/><w:left w:w="140" w:type="dxa"/>'
          f'<w:bottom w:w="70" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tcMar></w:tcPr>{code_p}</w:tc></w:tr></w:tbl>')
    add(empty(60))
    add(para(run("Anexo B. Evidencia y panel web", b=True, sz=BODY_SZ), after=60, keep_next=True))
    add(body_p("Con el servidor iniciado, el panel queda en http://127.0.0.1:8000. La evidencia de los escenarios está "
               "en las carpetas docs/evidencia y docs/evidencia_ollama del repositorio.", after=0))

    body = "".join(parts)
    body = body.replace("@@TOC@@", build_toc(toc_pages))
    return body


def build_toc(pages: dict[str, int]) -> str:
    out = [para(run("Contenidos", b=True, sz=34), after=160)]
    n = len(BOOKMARKS)
    for idx, (level, text, name) in enumerate(BOOKMARKS):
        first, last = idx == 0, idx == n - 1
        page = str(pages.get(name, 0))
        begin = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\h \\u \\z '
                 '\\t "Heading 1,1,Heading 2,2," </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>') if first else ""
        end = '<w:r><w:fldChar w:fldCharType="end"/></w:r>' if last else ""
        b = level == 1
        rpr = f'<w:b w:val="{1 if b else 0}"/><w:color w:val="000000"/><w:sz w:val="22"/><w:szCs w:val="22"/>'
        link = (f'<w:hyperlink w:anchor="{name}"><w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'
                f'<w:r><w:rPr>{rpr}</w:rPr><w:tab/><w:t>{page}</w:t></w:r></w:hyperlink>')
        ind = "0" if level == 1 else "360"
        before = "160" if level == 1 and idx else "40"
        out.append(f'<w:p><w:pPr><w:tabs><w:tab w:val="right" w:leader="none" w:pos="{W}"/></w:tabs>'
                   f'<w:spacing w:before="{before}" w:after="0" w:line="240" w:lineRule="auto"/>'
                   f'<w:ind w:left="{ind}" w:firstLine="0"/><w:jc w:val="left"/></w:pPr>{begin}{link}{end}</w:p>')
    return "".join(out)


# ------------------------------------------------------------------ ensamblado del paquete
def build(template: Path, toc_pages: dict[str, int]) -> dict[str, tuple[int, str]]:
    tmp = Path(tempfile.mkdtemp(prefix="informe_duoc_"))
    with zipfile.ZipFile(template) as z:
        z.extractall(tmp)

    # imágenes
    media = tmp / "word" / "media"
    files = {"arq": ("arquitectura_simple.png", ROOT / "docs" / "diagramas" / "arquitectura_simple.png"),
             "flujo": ("flujo_simple.png", ROOT / "docs" / "diagramas" / "flujo_simple.png")}
    from PIL import Image
    for key, (_, src) in files.items():
        with Image.open(src) as im:
            SIZES[key] = im.size
    rels_path = tmp / "word" / "_rels" / "document.xml.rels"
    rels = rels_path.read_text(encoding="utf-8")
    rids = {}
    for i, (key, (name, src)) in enumerate(files.items(), start=20):
        shutil.copy(src, media / name)
        rids[key] = f"rId{i}"
        rels = rels.replace("</Relationships>",
                            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                            f'relationships/image" Target="media/{name}"/></Relationships>')
    rels_path.write_text(rels, encoding="utf-8")
    ct = (tmp / "[Content_Types].xml").read_text(encoding="utf-8")
    if 'Extension="jpg"' not in ct:
        ct = ct.replace("<Default ContentType=\"image/png\" Extension=\"png\"/>",
                        "<Default ContentType=\"image/png\" Extension=\"png\"/>"
                        "<Default ContentType=\"image/jpeg\" Extension=\"jpg\"/>")
    (tmp / "[Content_Types].xml").write_text(ct, encoding="utf-8")

    # cuerpo
    doc_path = tmp / "word" / "document.xml"
    xml = doc_path.read_text(encoding="utf-8")
    head = xml[: xml.index("<w:body>") + len("<w:body>")]
    for ns in NS_REQUIRED:
        assert ns in head, f"falta {ns} en la plantilla"
    sect = re.findall(r"<w:sectPr>.*?</w:sectPr>", xml, flags=re.S)[-1]
    sect = sect.replace("1440.0000000000002", "1440").replace("1842.51968503937", "1843")
    body = build_body(toc_pages, rids)
    doc_path.write_text(head + body + sect + "</w:body></w:document>", encoding="utf-8")

    # encabezado de las páginas interiores
    h = tmp / "word" / "header1.xml"
    t = h.read_text(encoding="utf-8")
    t = t.replace("Nombre de documento", f"Informe de proyecto: {DOC_NAME}")
    t = t.replace("Nombre completo de la asignatura", COURSE)
    t = t.replace("Nombre de organización y/o equipo de trabajo", TEAM)
    h.write_text(t, encoding="utf-8")

    # limpieza de decimales que Word no acepta en algunos atributos
    for p in tmp.rglob("*.xml"):
        s = p.read_text(encoding="utf-8")
        s2 = s.replace("1440.0000000000002", "1440")
        if s2 != s:
            p.write_text(s2, encoding="utf-8")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        order = ["[Content_Types].xml", "_rels/.rels"]
        for name in order:
            z.write(tmp / name, name)
        for p in sorted(tmp.rglob("*")):
            rel = p.relative_to(tmp).as_posix()
            if p.is_file() and rel not in order:
                z.write(p, rel)
    shutil.rmtree(tmp, ignore_errors=True)
    return {name: (lvl, text) for lvl, text, name in BOOKMARKS}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--toc", default="")
    args = ap.parse_args()
    pages = json.loads(Path(args.toc).read_text(encoding="utf-8")) if args.toc else {}
    marks = build(Path(args.template), pages)
    Path(OUT.with_suffix(".bookmarks.json")).write_text(json.dumps(marks, ensure_ascii=False), encoding="utf-8")
    print("Informe generado:", OUT, f"({len(marks)} encabezados)")
