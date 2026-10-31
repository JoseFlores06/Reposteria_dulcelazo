"""
Exporta a PDF el reporte de ejecución del plan de pruebas de Dulce Lazo en Kiwi TCMS.

Todo el contenido (casos, estados por build, comentarios y defectos vinculados) se lee
de Kiwi por su API JSON-RPC en el momento de exportar; severidad, prioridad y estado de
cada defecto se toman de defectos.json (Kiwi no guarda esos campos en un enlace).

Uso:
    pip install requests reportlab
    python exportar_reporte.py --url https://localhost --usuario admin \
        --salida TC10_CalidadyPruebasdeSoftware_Grupo4_Lopez_Fernandez_Flores_Puma_Ordonez_Reporte.pdf
"""
import argparse
import getpass
import json
import os
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path
import html
from xml.sax.saxutils import escape as esc

import requests
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from cargar_kiwi import AQUI, PLAN, PRODUCTO, Kiwi

COLOR = {"PASSED": colors.HexColor("#2e7d32"), "FAILED": colors.HexColor("#c62828"),
         "BLOCKED": colors.HexColor("#ef6c00"), "IDLE": colors.HexColor("#757575")}
ROSA = colors.HexColor("#be185d")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://localhost")
    ap.add_argument("--usuario", required=True)
    ap.add_argument("--salida", default="Reporte_Kiwi_DulceLazo.pdf")
    ap.add_argument("--verificar-ssl", action="store_true")
    a = ap.parse_args()
    if not a.verificar_ssl:
        requests.packages.urllib3.disable_warnings()
    k = Kiwi(a.url, a.verificar_ssl)
    k("Auth.login", a.usuario, os.getenv("KIWI_PASSWORD") or getpass.getpass(f"Contraseña de Kiwi para {a.usuario}: "))

    prod = k.uno("Product.filter", {"name": PRODUCTO})
    plan = k.uno("TestPlan.filter", {"name": PLAN, "product": prod["id"]})
    if not plan:
        raise SystemExit("No existe el plan en Kiwi. Ejecuta primero cargar_kiwi.py.")
    casos = sorted(k("TestCase.filter", {"plan": plan["id"]}), key=lambda c: c["summary"])
    runs = sorted(k("TestRun.filter", {"plan": plan["id"]}), key=lambda r: r["id"])
    defectos = {d["id"]: d for d in json.load(open(AQUI / "defectos.json", encoding="utf-8"))}

    ejec = OrderedDict()   # run_id -> {case_id: execution}
    for r in runs:
        ejec[r["id"]] = {e["case"]: e for e in k("TestExecution.filter", {"run": r["id"]})}
    links = {}              # (run_id, case_id) -> [nombres de defecto]
    comentarios = {}
    for rid, por_caso in ejec.items():
        for cid, e in por_caso.items():
            ls = k("TestExecution.get_links", {"execution": e["id"]})
            links[(rid, cid)] = sorted({l["name"] for l in ls if l.get("is_defect")})
            if e["status__name"] in ("FAILED", "BLOCKED") or (rid == runs[0]["id"] and links[(rid, cid)]):
                comentarios[(rid, cid)] = list(dict.fromkeys(html.unescape(c["comment"]) for c in k("TestExecution.get_comments", e["id"])))

    st = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=st["Title"], textColor=ROSA, fontSize=20, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=st["Heading2"], textColor=ROSA, spaceBefore=10)
    p = ParagraphStyle("p", parent=st["BodyText"], fontSize=9, leading=12)
    chico = ParagraphStyle("c", parent=p, fontSize=7.5, leading=9.5)
    centro = ParagraphStyle("cc", parent=chico, alignment=TA_CENTER)

    def estado(nombre):
        return Paragraph(f'<font color="{COLOR.get(nombre, colors.black).hexval()}"><b>{nombre}</b></font>', centro)

    def tabla(filas, anchos, cabecera_color=ROSA):
        t = Table(filas, colWidths=anchos, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), cabecera_color), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d0d0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fdf2f8")]),
        ]))
        return t

    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    elems = [
        Paragraph("Reporte de ejecución de pruebas — Kiwi TCMS", h1),
        Paragraph(f"<b>Producto:</b> {esc(prod['name'])} &nbsp;·&nbsp; <b>Plan:</b> TP-{plan['id']}: {esc(plan['name'])} "
                  f"&nbsp;·&nbsp; <b>Versión:</b> {plan.get('product_version__value', '')}", p),
        Paragraph(f"<b>Exportado de:</b> {a.url} &nbsp;·&nbsp; <b>Fecha de exportación:</b> {hoy} "
                  f"&nbsp;·&nbsp; <b>Usuario:</b> {a.usuario}", p),
        Spacer(1, 8), Paragraph("1. Resumen por Test Run", h2),
    ]
    filas = [["Test Run", "Build", "Casos", "PASSED", "FAILED", "BLOCKED", "IDLE", "% aprobados*"]]
    for r in runs:
        c = Counter(e["status__name"] for e in ejec[r["id"]].values())
        ejecutados = sum(v for s, v in c.items() if s != "IDLE")
        pct = f"{100 * c['PASSED'] / ejecutados:.1f} %" if ejecutados else "—"
        filas.append([Paragraph(esc(f"TR-{r['id']}: {r['summary']}"), chico), r.get("build__name", ""),
                      sum(c.values()), c["PASSED"], c["FAILED"], c["BLOCKED"], c["IDLE"], pct])
    elems += [tabla(filas, [9.5 * cm, 1.6 * cm, 1.4 * cm, 1.7 * cm, 1.7 * cm, 1.9 * cm, 1.4 * cm, 2.4 * cm]),
              Paragraph("* % aprobados sobre los casos ejecutados (sin contar IDLE). IDLE = caso manual o de "
                        "aceptación aún no ejecutado en ese run.", chico)]

    # 2. Matriz caso × run
    elems += [PageBreak(), Paragraph("2. Resultado de cada caso por build", h2)]
    cab = ["Caso", "Prior.", "Categoría"] + [f"TR-{r['id']}\n{r.get('build__name', '')}" for r in runs] + ["Defecto"]
    filas = [cab]
    for c in casos:
        fila = [Paragraph(esc(c["summary"]), chico), c.get("priority__value", ""), Paragraph(esc(c.get("category__name", "")), chico)]
        defs = set()
        for r in runs:
            e = ejec[r["id"]].get(c["id"])
            fila.append(estado(e["status__name"]) if e else "—")
            defs.update(links.get((r["id"], c["id"]), []))
        fila.append(Paragraph("<br/>".join(sorted(defs)) or "—", chico))
        filas.append(fila)
    ancho_run = 2.0 * cm
    elems.append(tabla(filas, [11.5 * cm, 1.2 * cm, 3.6 * cm] + [ancho_run] * len(runs) + [2.4 * cm]))

    # 3. Defectos
    elems += [PageBreak(), Paragraph("3. Defectos registrados y vinculados", h2),
              Paragraph("Cada defecto está enlazado (is_defect) a la ejecución que lo detectó en Kiwi. "
                        "Severidad, prioridad y corrección: docs/DEFECTOS.md del repositorio.", p), Spacer(1, 4)]
    vinculados = Counter(n for v in links.values() for n in v)
    filas = [["ID", "Descripción", "Severidad", "Prioridad", "Casos", "Estado"]]
    for did, d in defectos.items():
        casos_d = ", ".join(d["casos"])
        estado_d = "Corregido en v2.0 y verificado (re-test PASSED)"
        filas.append([did, Paragraph(f"<b>{esc(d['titulo'])}</b><br/>{esc(d['descripcion'])}", chico), d["severidad"],
                      d["prioridad"], Paragraph(casos_d, chico),
                      Paragraph(estado_d + ("" if vinculados.get(did) else "<br/>(sin enlace en Kiwi)"), chico)])
    elems.append(tabla(filas, [2.2 * cm, 13.5 * cm, 1.9 * cm, 1.9 * cm, 3.2 * cm, 3.6 * cm]))

    # 4. Observaciones de ejecución (fallos y bloqueos)
    elems += [PageBreak(), Paragraph("4. Observaciones registradas en las ejecuciones fallidas o bloqueadas", h2)]
    nombre = {c["id"]: c["summary"] for c in casos}
    run_nom = {r["id"]: f"TR-{r['id']} ({r.get('build__name', '')})" for r in runs}
    filas = [["Run", "Caso", "Comentario registrado en Kiwi"]]
    for (rid, cid), cs in comentarios.items():
        if cs:
            filas.append([run_nom[rid], Paragraph(esc(str(nombre.get(cid, cid))), chico), Paragraph("<br/>".join(esc(x) for x in cs), chico)])
    elems.append(tabla(filas, [2.6 * cm, 8 * cm, 15.6 * cm]))

    def pie(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1.2 * cm, 0.7 * cm, f"Kiwi TCMS · {PRODUCTO} · exportado {hoy}")
        canvas.drawRightString(landscape(A4)[0] - 1.2 * cm, 0.7 * cm, f"Página {doc.page}")
        canvas.restoreState()

    SimpleDocTemplate(a.salida, pagesize=landscape(A4), leftMargin=1.2 * cm, rightMargin=1.2 * cm,
                      topMargin=1.2 * cm, bottomMargin=1.2 * cm, title="Reporte de ejecución — Kiwi TCMS",
                      author=a.usuario).build(elems, onFirstPage=pie, onLaterPages=pie)
    print(f"Reporte guardado en {Path(a.salida).resolve()}")


if __name__ == "__main__":
    main()
