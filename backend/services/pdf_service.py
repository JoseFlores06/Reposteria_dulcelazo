"""
Generador de Boleta de Venta según formato SUNAT (Perú).
Formato: Cabecera empresa | Caja Documento | Datos cliente | Detalle | Totales IGV | Monto en letras | Pie
"""
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String as GString
from reportlab.graphics import renderPDF

# Paleta de colores Dulce Lazo
ROSA_OSC   = colors.HexColor("#9d174d")   # títulos principales
ROSA_MED   = colors.HexColor("#db2777")   # cabecera tabla
ROSA_CAJA  = colors.HexColor("#be185d")   # caja número de boleta
ROSA_SUAVE = colors.HexColor("#fce7f3")   # fondo filas alternas
GRIS_LINEA = colors.HexColor("#e5e7eb")
NEGRO      = colors.HexColor("#111827")
GRIS_TEXT  = colors.HexColor("#6b7280")


# Conversión de monto a letras (español peruano)

def _conv_entero(n: int) -> str:
    if n == 0:
        return "CERO"
    unid = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE",
            "OCHO", "NUEVE", "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE",
            "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE",
            "VEINTE", "VEINTIUN", "VEINTIDOS", "VEINTITRES", "VEINTICUATRO",
            "VEINTICINCO", "VEINTISEIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE"]
    decen = ["", "", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
             "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
    centen = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
              "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]

    def _bloque(x):
        if x == 0:
            return ""
        if x < 30:
            return unid[x]
        if x < 100:
            d, u = divmod(x, 10)
            return decen[d] + (" Y " + unid[u] if u else "")
        if x == 100:
            return "CIEN"
        c, r = divmod(x, 100)
        return centen[c] + (" " + _bloque(r) if r else "")

    if n < 1000:
        return _bloque(n)
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        mil = "MIL" if m == 1 else _bloque(m) + " MIL"
        return mil + (" " + _bloque(r) if r else "")
    return str(n)


def monto_a_letras(monto: float) -> str:
    entero = int(monto)
    centavos = round((monto - entero) * 100)
    return f"SON: {_conv_entero(entero)} Y {centavos:02d}/100 SOLES"


# PDF principal

def generar_boleta_pdf(venta, empresa) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    def estilo(nombre, **kw):
        defaults = dict(fontName="Helvetica", fontSize=9, leading=12)
        defaults.update(kw)
        return ParagraphStyle(nombre, parent=styles["Normal"], **defaults)

    s_empresa    = estilo("empresa",    fontSize=16, fontName="Helvetica-Bold",
                          textColor=ROSA_OSC, alignment=TA_LEFT, leading=20)
    s_sub        = estilo("sub",        fontSize=8,  textColor=GRIS_TEXT, alignment=TA_LEFT, leading=11)
    s_caja_tipo  = estilo("caja_tipo",  fontSize=11, fontName="Helvetica-Bold",
                          textColor=colors.white, alignment=TA_CENTER, leading=14)
    s_caja_num   = estilo("caja_num",   fontSize=10, fontName="Helvetica-Bold",
                          textColor=colors.white, alignment=TA_CENTER, leading=13)
    s_seccion    = estilo("seccion",    fontSize=8,  fontName="Helvetica-Bold",
                          textColor=ROSA_MED, leading=10)
    s_dato_k     = estilo("dato_k",     fontSize=8,  fontName="Helvetica-Bold",
                          textColor=NEGRO, leading=11)
    s_dato_v     = estilo("dato_v",     fontSize=8,  textColor=NEGRO, leading=11)
    s_th         = estilo("th",         fontSize=8,  fontName="Helvetica-Bold",
                          textColor=colors.white, alignment=TA_CENTER, leading=11)
    s_td_c       = estilo("td_c",       fontSize=8,  alignment=TA_CENTER, leading=11)
    s_td_r       = estilo("td_r",       fontSize=8,  alignment=TA_RIGHT,  leading=11)
    s_td_l       = estilo("td_l",       fontSize=8,  leading=11)
    s_total_k    = estilo("total_k",    fontSize=9,  fontName="Helvetica-Bold",
                          alignment=TA_RIGHT, textColor=NEGRO)
    s_total_gran = estilo("total_gran", fontSize=11, fontName="Helvetica-Bold",
                          alignment=TA_RIGHT, textColor=ROSA_OSC)
    s_letras     = estilo("letras",     fontSize=8,  fontName="Helvetica-Bold",
                          textColor=NEGRO, leading=11)
    s_pie        = estilo("pie",        fontSize=7,  textColor=GRIS_TEXT,
                          alignment=TA_CENTER, leading=10)

    e = elementos = []

    # 1. CABECERA: empresa (izq) + caja boleta (der)
    nombre_empresa = getattr(empresa, "nombre", None) or "DULCE LAZO"
    ruc            = getattr(empresa, "ruc",      None) or ""
    direccion      = getattr(empresa, "direccion", None) or ""
    distrito       = getattr(empresa, "distrito",  None) or ""
    telefono       = getattr(empresa, "telefono",  None) or ""
    correo         = getattr(empresa, "correo",    None) or ""
    yape           = getattr(empresa, "numero_yape_plin", None) or ""

    # Columna izquierda: datos empresa
    col_empresa = [
        Paragraph(nombre_empresa.upper(), s_empresa),
    ]
    if ruc:
        col_empresa.append(Paragraph(f"RUC: {ruc}", estilo("ruc", fontSize=9, fontName="Helvetica-Bold", textColor=ROSA_OSC)))
    if direccion:
        ubigeo = f"{direccion}{', ' + distrito if distrito else ''}"
        col_empresa.append(Paragraph(ubigeo, s_sub))
    if telefono:
        col_empresa.append(Paragraph(f"Teléf.: {telefono}", s_sub))
    if correo:
        col_empresa.append(Paragraph(correo, s_sub))
    if yape:
        col_empresa.append(Paragraph(f"Yape/Plin: {yape}", s_sub))

    # Columna derecha: caja tipo documento
    serie = "B001"
    numero = f"{venta.id:08d}"
    col_caja = Table(
        [
            [Paragraph("BOLETA DE VENTA", s_caja_tipo)],
            [Paragraph("ELECTRÓNICA", s_caja_tipo)],
            [Paragraph(f"{serie} - {numero}", s_caja_num)],
        ],
        colWidths=[6 * cm],
    )
    col_caja.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ROSA_CAJA),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEABOVE",     (0, 1), (-1, 1), 0.5, colors.HexColor("#ec4899")),
        ("LINEABOVE",     (0, 2), (-1, 2), 0.5, colors.HexColor("#ec4899")),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))

    tabla_header = Table(
        [[col_empresa, col_caja]],
        colWidths=[10.5 * cm, 6.5 * cm],
    )
    tabla_header.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN",        (1, 0), (1, 0), "RIGHT"),
    ]))
    e.append(tabla_header)
    e.append(Spacer(1, 3 * mm))
    e.append(HRFlowable(width="100%", thickness=1.5, color=ROSA_MED))
    e.append(Spacer(1, 3 * mm))

    # 2. DATOS DEL COMPROBANTE
    fecha_emision = venta.fecha_hora or datetime.now()
    fecha_str     = fecha_emision.strftime("%d/%m/%Y")
    hora_str      = fecha_emision.strftime("%H:%M")

    cliente_nombre = "CONSUMIDOR FINAL"
    if venta.cliente:
        cliente_nombre = f"{venta.cliente.nombres} {venta.cliente.apellidos}".strip().upper()
    cliente_tel = getattr(venta.cliente, "telefono", "") or ""

    vendedor = ""
    if venta.colaborador:
        vendedor = f"{venta.colaborador.nombres} {venta.colaborador.apellidos}".strip()

    def fila_dato(label, valor):
        return [Paragraph(label, s_dato_k), Paragraph(str(valor), s_dato_v)]

    datos_comp = [
        fila_dato("Fecha de emisión:", fecha_str),
        fila_dato("Hora:", hora_str),
        fila_dato("Señor(es):", cliente_nombre),
    ]
    if cliente_tel:
        datos_comp.append(fila_dato("Teléfono cliente:", cliente_tel))
    datos_comp.append(fila_dato("Forma de pago:", venta.metodo_pago.value.capitalize() if venta.metodo_pago else "—"))
    if vendedor:
        datos_comp.append(fila_dato("Atendido por:", vendedor))
    # Dirección de entrega
    dir_entrega = getattr(venta, "direccion_entrega", None)
    if dir_entrega:
        datos_comp.append(fila_dato("Dirección de entrega:", dir_entrega))
    else:
        datos_comp.append(fila_dato("Dirección de entrega:", "Recojo en tienda"))
    if venta.fecha_entrega:
        fe = venta.fecha_entrega.strftime("%d/%m/%Y %H:%M")
        datos_comp.append(fila_dato("Fecha de entrega:", fe))

    tabla_datos = Table(datos_comp, colWidths=[4 * cm, 13 * cm])
    tabla_datos.setStyle(TableStyle([
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.white, colors.HexColor("#fdf2f8")]),
    ]))
    e.append(tabla_datos)
    e.append(Spacer(1, 3 * mm))
    e.append(HRFlowable(width="100%", thickness=0.8, color=GRIS_LINEA))
    e.append(Spacer(1, 3 * mm))

    # 3. DETALLE DE PRODUCTOS
    encabezados = [
        Paragraph("CANT.", s_th),
        Paragraph("UNID.", s_th),
        Paragraph("DESCRIPCIÓN DEL BIEN O SERVICIO", s_th),
        Paragraph("P. UNIT. (S/)", s_th),
        Paragraph("IMPORTE (S/)", s_th),
    ]
    filas = [encabezados]
    for item in venta.items:
        precio_u = float(item.precio_unitario_snapshot)
        subtotal = float(item.subtotal)
        filas.append([
            Paragraph(str(item.cantidad), s_td_c),
            Paragraph("UND", s_td_c),
            Paragraph(item.nombre_snapshot, s_td_l),
            Paragraph(f"{precio_u:.2f}", s_td_r),
            Paragraph(f"{subtotal:.2f}", s_td_r),
        ])

    tabla_items = Table(
        filas,
        colWidths=[1.5 * cm, 1.5 * cm, 9.5 * cm, 2.8 * cm, 2.7 * cm],
        repeatRows=1,
    )
    tabla_items.setStyle(TableStyle([
        # Encabezado
        ("BACKGROUND",    (0, 0), (-1, 0), ROSA_MED),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        # Filas
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, ROSA_SUAVE]),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRIS_LINEA),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        # Alineación columnas numéricas
        ("ALIGN",         (0, 0), (1, -1), "CENTER"),
        ("ALIGN",         (3, 0), (4, -1), "RIGHT"),
    ]))
    e.append(tabla_items)
    e.append(Spacer(1, 3 * mm))

    # 4. TOTALES + IGV
    total = float(venta.total)
    # En Perú el IGV es 18%. Para boleta de consumidor final,
    # el precio ya incluye IGV. Calculamos el desglose:
    op_gravada = round(total / 1.18, 2)
    igv        = round(total - op_gravada, 2)

    totales_filas = [
        [Paragraph("OP. GRAVADA    S/", s_total_k), Paragraph(f"{op_gravada:.2f}", s_td_r)],
        [Paragraph("IGV 18%        S/", s_total_k), Paragraph(f"{igv:.2f}", s_td_r)],
        [Paragraph("TOTAL          S/", s_total_gran), Paragraph(f"{total:.2f}",
            estilo("tv", fontSize=12, fontName="Helvetica-Bold",
                   alignment=TA_RIGHT, textColor=ROSA_OSC))],
    ]
    tabla_totales = Table(totales_filas, colWidths=[13.5 * cm, 4.5 * cm])
    tabla_totales.setStyle(TableStyle([
        ("LINEABOVE",    (0, 0), (-1, 0), 0.5, GRIS_LINEA),
        ("LINEABOVE",    (0, 2), (-1, 2), 1.2, ROSA_MED),
        ("BACKGROUND",   (0, 2), (-1, 2), ROSA_SUAVE),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    e.append(tabla_totales)
    e.append(Spacer(1, 3 * mm))

    # 5. MONTO EN LETRAS
    letras = monto_a_letras(total)
    caja_letras = Table(
        [[Paragraph(letras, s_letras)]],
        colWidths=[18 * cm],
    )
    caja_letras.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 0.8, ROSA_MED),
        ("BACKGROUND",   (0, 0), (-1, -1), ROSA_SUAVE),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    e.append(caja_letras)
    e.append(Spacer(1, 4 * mm))

    # 6. NOTAS
    if venta.notas:
        e.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_LINEA))
        e.append(Spacer(1, 2 * mm))
        e.append(Paragraph(f"<b>Observaciones:</b> {venta.notas}",
                            estilo("obs", fontSize=8, textColor=GRIS_TEXT)))
        e.append(Spacer(1, 2 * mm))

    # 7. PIE DE PÁGINA
    e.append(HRFlowable(width="100%", thickness=1, color=ROSA_MED))
    e.append(Spacer(1, 2 * mm))
    """
    e.append(Paragraph(
        "Representación impresa de Boleta de Venta — Autorizado por SUNAT",
        s_pie,
    ))
    e.append(Paragraph(
        f"Para validar este comprobante ingrese a: <b>www.sunat.gob.pe</b>  |  "
        f"RUC: {ruc or '—'}  |  Serie: {serie}  |  N°: {numero}",
        s_pie,
    ))"""
    e.append(Spacer(1, 2 * mm))
    e.append(Paragraph(
        f"¡Gracias por su preferencia! Hecho con amor artesanal — {nombre_empresa}  🧁",
        estilo("gracias", fontSize=9, fontName="Helvetica-Bold",
               textColor=ROSA_OSC, alignment=TA_CENTER),
    ))

    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
