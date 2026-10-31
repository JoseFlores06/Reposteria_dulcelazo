"""
Carga el proyecto Dulce Lazo en Kiwi TCMS y registra los resultados de las pruebas.

Qué hace (se puede ejecutar varias veces: reutiliza lo que ya existe):
  1. Crea el producto «Dulce Lazo», la versión «2026-II» y los builds v1.0 y v2.0.
  2. Crea las categorías y los 60 casos de prueba de casos_tc9.json
     (56 del TC9 + 4 nuevos), en estado CONFIRMED, con Setup / Pasos / Resultado esperado.
  3. Crea el plan «Plan de Pruebas — Dulce Lazo (TC10)» y le agrega todos los casos.
  4. Por cada archivo JUnit (pytest --junitxml) crea un Test Run contra su build y marca
     cada caso PASSED / FAILED / BLOCKED según el resultado real de su prueba, con un
     comentario y el vínculo al defecto. Los casos sin prueba automatizada quedan IDLE.
  5. Crea el Test Run «Demo en vivo — Build v2.0» con los casos que se ejecutan en clase,
     todos en IDLE para marcarlos frente al docente.

Uso (Kiwi en Docker según la guía de la Semana 5):
    pip install requests
    python cargar_kiwi.py --url https://localhost --usuario admin \
        --v1 resultados/v1.0_funcionales.xml --v2 resultados/v2.0_funcionales.xml

La contraseña se pide por teclado (o variable de entorno KIWI_PASSWORD).
"""
import argparse
import base64
import getpass
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
REPO_URL = "https://github.com/JoseFlores06/Reposteria_dulcelazo"
PRODUCTO, VERSION = "Dulce Lazo", "2026-II"
PLAN = "Plan de Pruebas — Dulce Lazo (TC10)"
PRIORIDAD = {"Crítica": "P1", "Alta": "P2", "Media": "P3", "Baja": "P4"}
CASOS_DEMO = ["TC-049", "TC-044", "TC-040", "TC-UAT-001"]


class Kiwi:
    """Cliente JSON-RPC mínimo de Kiwi TCMS (sesión por cookie)."""

    def __init__(self, url, verificar_ssl):
        self.url = url.rstrip("/") + "/json-rpc/"
        self.s = requests.Session()
        self.s.verify = verificar_ssl
        self._id = 0

    def __call__(self, metodo, *params):
        self._id += 1
        r = self.s.post(self.url, json={"jsonrpc": "2.0", "method": metodo, "params": list(params), "id": self._id})
        r.raise_for_status()
        cuerpo = r.json()
        if "error" in cuerpo:
            raise RuntimeError(f"{metodo}: {cuerpo['error'].get('message', cuerpo['error'])}")
        return cuerpo["result"]

    def uno(self, metodo, filtro):
        res = self(metodo, filtro)
        return res[0] if res else None


def texto_caso(c):
    """Kiwi guarda el caso en un solo campo; convención del curso: Setup / Pasos / Resultado Esperado."""
    return (
        f"**Requisito / criterio:** {c['requisito']}\n\n"
        f"**Criterio de aceptación:** {c['criterio']}\n\n"
        f"**Tipo de caso:** {c['cod_tipo']} — {c['tipo']} · **Nivel:** {c['nivel']}\n\n"
        f"## Setup\n\n{c['precondiciones']}\n\n"
        f"**Datos de entrada:**\n\n```\n{c['datos']}\n```\n\n"
        f"## Pasos\n\n{c['pasos']}\n\n"
        f"## Resultado Esperado\n\n{c['esperado']}\n\n"
        f"---\nAutomatización: {c['funcion_texto'] or '— (caso manual)'}"
    )


def leer_junit(ruta):
    """{'TC-012': ('PASSED'|'FAILED'|'BLOCKED', mensaje)} a partir de pytest --junitxml."""
    resultados = {}
    for tc in ET.parse(ruta).iter("testcase"):
        m = re.match(r"test_TC(\d{3})_", tc.get("name", ""))
        if not m:
            continue
        caso = f"TC-{m.group(1)}"
        falla = tc.find("failure")
        if falla is None:
            falla = tc.find("error")
        omitida = tc.find("skipped")
        if falla is not None:
            msg = (falla.get("message") or falla.text or "").strip().splitlines()[0][:400]
            resultados[caso] = ("FAILED", msg)
        elif omitida is not None:
            resultados[caso] = ("BLOCKED", (omitida.get("message") or "").replace("BLOQUEADO: ", ""))
        else:
            resultados[caso] = ("PASSED", "")
    return resultados


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://localhost", help="URL de Kiwi (p. ej. https://localhost:8443)")
    ap.add_argument("--usuario", required=True)
    ap.add_argument("--v1", help="JUnit XML de las pruebas funcionales sobre la v1.0")
    ap.add_argument("--v2", help="JUnit XML de las pruebas funcionales sobre la v2.0")
    ap.add_argument("--unitarias-v2", help="JUnit XML de las pruebas unitarias (se adjunta al run v2.0)")
    ap.add_argument("--issues", help="JSON {\"DEF-DL-001\": \"https://github.com/.../issues/1\", ...}")
    ap.add_argument("--verificar-ssl", action="store_true", help="Kiwi local usa certificado propio: por defecto no se verifica")
    a = ap.parse_args()

    if not a.verificar_ssl:
        requests.packages.urllib3.disable_warnings()
    clave = os.getenv("KIWI_PASSWORD") or getpass.getpass(f"Contraseña de Kiwi para {a.usuario}: ")
    k = Kiwi(a.url, a.verificar_ssl)
    k("Auth.login", a.usuario, clave)
    yo = k.uno("User.filter", {"username": a.usuario}) if "User.filter" in k("system.listMethods") else None
    yo_id = yo["id"] if yo else None
    print(f"Conectado a {a.url} como {a.usuario}")

    casos = json.load(open(AQUI / "casos_tc9.json", encoding="utf-8"))
    defectos = {d["id"]: d for d in json.load(open(AQUI / "defectos.json", encoding="utf-8"))}
    issues = json.load(open(a.issues, encoding="utf-8")) if a.issues else {}
    defecto_de_caso = {c: d for d in defectos.values() for c in d["casos"]}

    # 1. Producto, versión y builds -------------------------------------------------
    clasif = k.uno("Classification.filter", {"name": "Software"}) or k("Classification.create", {"name": "Software"})
    prod = k.uno("Product.filter", {"name": PRODUCTO}) or k("Product.create", {
        "name": PRODUCTO, "classification": clasif["id"],
        "description": "Sistema ERP para Pastelería – Dulce Lazo (Grupo 4, Calidad y Pruebas de Software, UPN)"})
    ver = k.uno("Version.filter", {"product": prod["id"], "value": VERSION}) or \
        k("Version.create", {"product": prod["id"], "value": VERSION})
    builds = {}
    for nombre in ("v1.0", "v2.0"):
        builds[nombre] = k.uno("Build.filter", {"version": ver["id"], "name": nombre}) or \
            k("Build.create", {"name": nombre, "version": ver["id"], "is_active": True})
    print(f"Producto {PRODUCTO} · versión {VERSION} · builds v1.0 y v2.0 listos")

    # 2. Categorías y casos ----------------------------------------------------------
    confirmado = k.uno("TestCaseStatus.filter", {"name": "CONFIRMED"})["id"]
    prioridades = {p["value"]: p["id"] for p in k("Priority.filter", {})}
    categorias, ids = {}, {}
    for c in casos:
        cat = c["categoria"]
        if cat not in categorias:
            categorias[cat] = k.uno("Category.filter", {"product": prod["id"], "name": cat}) or \
                k("Category.create", {"name": cat, "product": prod["id"]})
        existente = k.uno("TestCase.filter", {"category__product": prod["id"], "summary__startswith": c["id"] + " ·"})
        valores = {
            "summary": c["summary"], "text": texto_caso(c), "category": categorias[cat]["id"],
            "product": prod["id"], "case_status": confirmado, "priority": prioridades[PRIORIDAD[c["prioridad"]]],
            "is_automated": bool(c["automatizado"]),
            "script": f"backend/tests/funcionales/test_casos_funcionales.py::{c['funcion_pytest']}*" if c["funcion_pytest"] else "",
            "requirement": c["requisito"], "notes": f"Origen: plantilla del TC9 · {c['nivel']}",
        }
        if existente:
            caso = existente
            k("TestCase.update", caso["id"], {x: valores[x] for x in valores if x != "product"})
        else:
            caso = k("TestCase.create", valores)
            for tag in [c["cod_tipo"], *re.findall(r"REQ-\d{3}", c["requisito"])]:
                k("TestCase.add_tag", caso["id"], tag)
        ids[c["id"]] = caso["id"]
    print(f"{len(ids)} casos de prueba en estado CONFIRMED")

    # 3. Plan --------------------------------------------------------------------------
    tipo = k.uno("PlanType.filter", {"name": "Acceptance"}) or k("PlanType.filter", {})[0]
    plan = k.uno("TestPlan.filter", {"name": PLAN, "product": prod["id"]}) or k("TestPlan.create", {
        "name": PLAN, "product": prod["id"], "product_version": ver["id"], "type": tipo["id"], "is_active": True,
        "text": "Casos funcionales y de aceptación del TC9 (+4 nuevos del TC10). Automatizados con pytest a nivel "
                f"API sobre MySQL/MariaDB ({REPO_URL}/tree/main/backend/tests/funcionales). "
                "Build v1.0 = software del TC6; build v2.0 = correcciones de los defectos DEF-DL-001 a DEF-DL-011."})
    en_plan = {c["id"] for c in k("TestCase.filter", {"plan": plan["id"]})}
    for cid in ids.values():
        if cid not in en_plan:
            k("TestPlan.add_case", plan["id"], cid)
    print(f"Plan «{PLAN}» con {len(ids)} casos")

    status = {s["name"]: s["id"] for s in k("TestExecutionStatus.filter", {})}

    def crear_run(resumen, build, casos_run, notas):
        run = k.uno("TestRun.filter", {"summary": resumen, "plan": plan["id"]})
        if not run:
            datos = {"summary": resumen, "plan": plan["id"], "build": build["id"], "notes": notas}
            if yo_id:
                datos["manager"] = yo_id
            run = k("TestRun.create", datos)
        actuales = {e["case"]: e for e in k("TestExecution.filter", {"run": run["id"]})}
        for cid in casos_run:
            if cid not in actuales:
                k("TestRun.add_case", run["id"], cid)
        ejecuciones = {e["case"]: e for e in k("TestExecution.filter", {"run": run["id"]})}
        return run, ejecuciones

    # 4. Runs con los resultados reales ----------------------------------------------
    for etiqueta, ruta in (("v1.0", a.v1), ("v2.0", a.v2)):
        if not ruta:
            continue
        resultados = leer_junit(ruta)
        fecha = datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%d/%m/%Y %H:%M")
        run, ejec = crear_run(
            f"Ejecución automatizada (pytest) — Build {etiqueta}", builds[etiqueta], list(ids.values()),
            f"Resultados de pytest --junitxml ({Path(ruta).name}, {fecha}). Casos sin prueba automatizada quedan IDLE.")
        cuenta = {}
        for caso_id, (estado, msg) in resultados.items():
            e = ejec.get(ids.get(caso_id))
            if not e:
                continue
            k("TestExecution.update", e["id"], {"status": status[estado], "build": builds[etiqueta]["id"]})
            texto = f"[{etiqueta}] {estado} — pytest ({fecha})."
            if msg:
                texto += f" Observado: {msg.rstrip('.')}."
            d = defecto_de_caso.get(caso_id)
            if d and estado == "FAILED":
                texto += f" Defecto: {d['id']} ({d['titulo']})."
            if d and etiqueta == "v2.0" and estado == "PASSED":
                texto += f" Re-test: {d['id']} corregido en v2.0 (commit {d['commit']})."
            if texto not in {html.unescape(x["comment"]) for x in k("TestExecution.get_comments", e["id"])}:
                k("TestExecution.add_comment", e["id"], texto)
            if d:
                url = issues.get(d["id"]) or f"{REPO_URL}/blob/tc10-v2.0/docs/DEFECTOS.md#{d['id'].lower()}"
                ya = {l["url"] for l in k("TestExecution.get_links", {"execution": e["id"]})}
                if url not in ya:
                    k("TestExecution.add_link", {"execution_id": e["id"], "url": url, "name": d["id"],
                                                 "is_defect": True}, False)
            cuenta[estado] = cuenta.get(estado, 0) + 1
        marca = datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m-%d %H:%M:%S")
        k("TestRun.update", run["id"], {"start_date": marca, "stop_date": marca})
        ya_adjuntos = {x.get("filename") for x in k("TestRun.list_attachments", run["id"])} \
            if "TestRun.list_attachments" in k("system.listMethods") else set()
        for adj in [ruta] + ([a.unitarias_v2] if etiqueta == "v2.0" and a.unitarias_v2 else []):
            if Path(adj).name in ya_adjuntos:
                continue
            k("TestRun.add_attachment", run["id"], Path(adj).name,
              base64.b64encode(Path(adj).read_bytes()).decode())
        print(f"Run {etiqueta}: {cuenta}  (id {run['id']})")

    # 5. Run para la demo en vivo ------------------------------------------------------
    run, _ = crear_run("Demo en vivo — Build v2.0", builds["v2.0"], [ids[c] for c in CASOS_DEMO if c in ids],
                       "Casos que el equipo ejecuta en vivo durante la sesión del TC10.")
    print(f"Run de demo con {len(CASOS_DEMO)} casos en IDLE (id {run['id']})")
    print("Listo. Abre TESTING → Search Test Runs para ver los resultados.")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        sys.exit("No se pudo conectar con Kiwi. ¿Está encendido? (docker compose up -d) ¿La URL es la correcta?")
