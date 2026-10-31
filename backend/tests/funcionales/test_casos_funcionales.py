"""
Casos de prueba funcionales automatizados — Dulce Lazo (TC9 → TC10).

Cada función lleva el ID del caso registrado en la plantilla del Trabajo de
Campo N.° 9 y en Kiwi TCMS (por ejemplo test_TC012_... ⇔ TC-012). Así el
script de carga a Kiwi puede asignar el resultado de cada prueba a su caso.

Nivel: integración / API (FastAPI TestClient) sobre MySQL/MariaDB real.
Google Calendar y Groq nunca se llaman de verdad: cuando el caso lo necesita
se reemplazan por dobles de prueba y así se indica en el docstring.
"""
import io
import time
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from jose import jwt

from models.cliente import Cliente
from models.colaborador import Colaborador
from models.empresa import Empresa
from models.insumo import Insumo
from models.merma_insumo import MermaInsumo
from models.producto import Producto
from models.usuario import Usuario
from models.venta import Venta

ADMIN = ("admin@dulcelazo.pe", "Admin12345!")  # mismos datos que conftest.py


# ----------------------------------------------------------------- utilidades

def _id_cliente(db, nombres, apellidos):
    return db.query(Cliente).filter_by(nombres=nombres, apellidos=apellidos).one().id


def _insumo(db, nombre):
    db.rollback()  # nueva transacción: ver lo que la API ya confirmó
    return db.query(Insumo).filter_by(nombre=nombre).one()


def _producto(db, nombre):
    return db.query(Producto).filter_by(nombre=nombre).one()


def _poner_stock(client, admin, db, nombre, stock):
    r = client.put(f"/api/insumos/{_insumo(db, nombre).id}", json={"stock_actual": stock}, headers=admin)
    assert r.status_code == 200, r.text


def _crear_producto(client, admin, nombre, receta, ganancia):
    """receta = [(insumo_id, cantidad), ...]"""
    import json
    insumos = [{"insumo_id": i, "cantidad_necesaria": c} for i, c in receta]
    r = client.post("/api/productos", headers=admin, data={
        "nombre": nombre, "porcentaje_ganancia": ganancia, "insumos_json": json.dumps(insumos),
    })
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _producto_huevos_x4(client, admin, db):
    """Precondición común: producto «Prueba Huevos x4» (receta Huevos 4, ganancia 50 %)."""
    return _crear_producto(client, admin, "Prueba Huevos x4", [(_insumo(db, "Huevos").id, 4)], 50)


def _vender(client, headers, cliente_id, items, **extra):
    body = {"cliente_id": cliente_id, "metodo_pago": "efectivo", "items": items, **extra}
    return client.post("/api/ventas", json=body, headers=headers)


def _crear_promocion(client, admin, nombre, item_tipo, item_id, pct, inicio=None, fin=None, activo=True):
    data = {"nombre": nombre, "item_tipo": item_tipo, "item_id": item_id,
            "porcentaje_descuento": pct, "activo": str(activo).lower()}
    if inicio:
        data["fecha_inicio"] = inicio
    if fin:
        data["fecha_fin"] = fin
    r = client.post("/api/promociones", data=data, headers=admin)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _texto_pdf(contenido: bytes) -> str:
    from pypdf import PdfReader
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(contenido)).pages)


RECETA_TORTA = [  # (insumo, cantidad) — receta de la Torta de Chocolate del seed
    ("Harina de trigo", 250), ("Azucar blanca", 200), ("Mantequilla", 150), ("Huevos", 4),
    ("Leche fresca", 200), ("Cacao en polvo", 100), ("Levadura seca", 10), ("Sal", 5),
]


# ============================================================ REQ-001 · Login

def test_TC001_login_valido_devuelve_token_y_rol(client):
    """TC-001 · CA-001 · T01 — credenciales correctas devuelven JWT y rol admin."""
    r = client.post("/api/auth/login", data={"username": ADMIN[0], "password": ADMIN[1]})
    assert r.status_code == 200
    cuerpo = r.json()
    assert len(cuerpo["access_token"].split(".")) == 3
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"]["correo"] == ADMIN[0]
    assert cuerpo["usuario"]["rol"] == "admin"


def test_TC002_login_invalido_devuelve_401_generico(client):
    """TC-002 · CA-002 · T22 — correo inexistente y clave incorrecta dan el mismo 401."""
    a = client.post("/api/auth/login", data={"username": "noexiste@dulcelazo.pe", "password": "Clave1234"})
    b = client.post("/api/auth/login", data={"username": ADMIN[0], "password": "Incorrecta9"})
    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"] == "Correo o contraseña incorrectos"
    assert "access_token" not in a.json() and "access_token" not in b.json()


# ==================================================== REQ-002 · Autorización

def test_TC003_admin_accede_a_finanzas(client, admin):
    """TC-003 · CA-003 · T24 — el administrador accede al dashboard de Finanzas."""
    r = client.get("/api/finanzas/dashboard", headers=admin)
    assert r.status_code == 200
    assert "totales" in r.json()


def test_TC004_vendedor_recibe_403_en_modulos_admin(client, vendedor):
    """TC-004 · CA-004 · T24 — el vendedor no puede leer módulos administrativos."""
    for ruta in ("/api/finanzas/dashboard", "/api/insumos", "/api/colaboradores", "/api/auth/usuarios"):
        r = client.get(ruta, headers=vendedor)
        assert r.status_code == 403, f"{ruta} devolvió {r.status_code} al vendedor"
        assert r.json()["detail"] == "Se requiere rol de administrador"


def test_TC005_recurso_protegido_sin_token_valido_da_401(client):
    """TC-005 · CA-005 · T25 — sin token, token inválido o token expirado → 401."""
    from auth import ALGORITHM, SECRET_KEY
    expirado = jwt.encode({"sub": ADMIN[0], "exp": datetime.utcnow() - timedelta(minutes=5)},
                          SECRET_KEY, algorithm=ALGORITHM)

    sin_token = client.get("/api/productos")
    assert sin_token.status_code == 401 and sin_token.json()["detail"] == "Not authenticated"
    for token in ("abc.123.xyz", expirado):
        r = client.get("/api/productos", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "No se pudieron validar las credenciales"


# ======================================================= REQ-003 · Insumos

def test_TC006_registrar_insumo_calcula_precio_unitario(client, admin):
    """TC-006 · CA-006 · T26 — Coco rallado 500 mg por S/ 6.00 → precio unitario 0.012."""
    r = client.post("/api/insumos", headers=admin, json={
        "nombre": "Coco rallado", "unidad": "mg", "cantidad_compra": 500, "precio_compra": 6.00})
    assert r.status_code == 200
    insumo = r.json()["insumo"]
    assert insumo["precio_unitario"] == pytest.approx(0.012)
    assert insumo["stock_actual"] == 500
    nombres = [i["nombre"] for i in client.get("/api/insumos", headers=admin).json()]
    assert "Coco rallado" in nombres


def test_TC007_insumo_con_stock_inicial_cero_se_registra(client, admin):
    """TC-007 · CA-007 · T03 — un insumo puede registrarse con stock 0 (aún no comprado)."""
    r = client.post("/api/insumos", headers=admin, json={
        "nombre": "Colorante rojo", "unidad": "ml", "cantidad_compra": 0, "precio_compra": 0})
    assert r.status_code == 200, r.text
    insumo = r.json()["insumo"]
    assert insumo["stock_actual"] == 0
    assert insumo["activo"] is True


# ============================================== REQ-004 · Alerta stock bajo

def test_TC008_venta_bajo_umbral_genera_alerta_y_evento(client, admin, vendedor, db, monkeypatch):
    """TC-008 · CA-008 · T39 — la venta que deja Huevos en 3 (< 4) devuelve la alerta
    legible y pide crear el evento de stock bajo. Google Calendar: doble de prueba
    (se captura el aviso que el sistema envía; con cuenta real se verifica en la demo)."""
    import routes.ventas as rv
    avisos = []
    monkeypatch.setattr(rv, "crear_evento_stock_bajo", lambda _db, ins: avisos.append(ins) or True)

    prod = _producto_huevos_x4(client, admin, db)
    _poner_stock(client, admin, db, "Huevos", 7)
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": prod, "cantidad": 1}])
    assert r.status_code == 200, r.text
    assert r.json()["alertas_stock"] == ["Huevos (3.0 unidad)"]
    assert len(avisos) == 1 and [i.nombre for i in avisos[0]] == ["Huevos"]


def test_TC009_alerta_sin_calendar_no_interrumpe_la_venta(client, admin, vendedor, db, capsys):
    """TC-009 · CA-009 · T44 — sin Google conectado la venta se registra y la alerta se muestra."""
    prod = _producto_huevos_x4(client, admin, db)
    _poner_stock(client, admin, db, "Huevos", 7)
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": prod, "cantidad": 1}])
    assert r.status_code == 200, r.text
    assert r.json()["alertas_stock"] == ["Huevos (3.0 unidad)"]
    assert float(_insumo(db, "Huevos").stock_actual) == 3
    assert "[Calendar] Error" not in capsys.readouterr().out


# =================================================== REQ-005 · Mermas

def test_TC010_merma_descuenta_stock_sin_cambiar_precio(client, admin, db):
    """TC-010 · CA-010 · T11 — baja de 150 mg de Mantequilla por vencimiento."""
    mant = _insumo(db, "Mantequilla")
    precio_antes = float(mant.precio_unitario)
    r = client.post(f"/api/insumos/{mant.id}/merma", headers=admin,
                    json={"cantidad": 150, "motivo": "vencido"})
    assert r.status_code == 200, r.text
    assert r.json()["insumo"]["stock_actual"] == 350
    assert r.json()["insumo"]["precio_unitario"] == pytest.approx(precio_antes)
    mermas = client.get("/api/insumos/mermas", headers=admin).json()
    assert mermas[0]["cantidad"] == 150 and mermas[0]["motivo"] == "vencido"


def test_TC011_merma_mayor_al_stock_se_rechaza(client, admin, db):
    """TC-011 · CA-011 · T30 — no se puede dar de baja más de lo que hay; mensaje legible."""
    mant = _insumo(db, "Mantequilla")
    r = client.post(f"/api/insumos/{mant.id}/merma", headers=admin,
                    json={"cantidad": 600, "motivo": "otro", "detalle": "Se dañó por humedad"})
    assert r.status_code == 400
    assert r.json()["detail"] == "No puedes dar de baja 600.00 mg: solo hay 500.00 mg en stock"
    assert float(_insumo(db, "Mantequilla").stock_actual) == 500
    assert db.query(MermaInsumo).count() == 0  # _insumo() ya abrió una transacción nueva


# ======================================= REQ-006 · Costeo de productos

def test_TC012_costo_y_precio_desde_receta(client, admin, db):
    """TC-012 · CA-012 · T11 — receta de la torta con 60 % → costo 9.53, venta 23.90."""
    receta = [(_insumo(db, n).id, c) for n, c in RECETA_TORTA]
    pid = _crear_producto(client, admin, "Torta de Chocolate TC-012", receta, 60)
    p = client.get(f"/api/productos/{pid}", headers=admin).json()
    assert p["precio_costo"] == pytest.approx(9.53)
    assert p["precio_venta"] == pytest.approx(23.90)


def test_TC013_ganancia_cero_precio_igual_al_costo(client, admin, db):
    """TC-013 · CA-013 · T03 — con 0 % de ganancia el precio de venta es el costo."""
    receta = [{"insumo_id": _insumo(db, n).id, "cantidad_necesaria": c} for n, c in RECETA_TORTA]
    r = client.post("/api/productos/costear", headers=admin,
                    json={"porcentaje_ganancia": 0, "insumos": receta})
    assert r.status_code == 200
    assert r.json()["precio_costo"] == pytest.approx(9.5325)
    assert r.json()["precio_venta"] == pytest.approx(9.53)


def test_TC038_precio_se_redondea_a_precio_peruano(client, admin, db):
    """TC-038 · T11 — costo 4.00 con 40 % → 6.67 se redondea a 6.90."""
    receta = [(_insumo(db, "Huevos").id, 4), (_insumo(db, "Manjar blanco").id, 1)]
    pid = _crear_producto(client, admin, "Prueba redondeo", receta, 40)
    p = client.get(f"/api/productos/{pid}", headers=admin).json()
    assert p["precio_costo"] == pytest.approx(4.00)
    assert p["precio_venta"] == pytest.approx(6.90)


def test_TC039_ganancia_100_se_rechaza_con_400(client, admin, db):
    """TC-039 · T04 — 100 % de ganancia es inválido (400, no 500); 99 % se acepta."""
    receta = [{"insumo_id": _insumo(db, "Huevos").id, "cantidad_necesaria": 4}]
    r99 = client.post("/api/productos/costear", headers=admin, json={"porcentaje_ganancia": 99, "insumos": receta})
    r100 = client.post("/api/productos/costear", headers=admin, json={"porcentaje_ganancia": 100, "insumos": receta})
    assert r99.status_code == 200
    assert r100.status_code == 400
    assert "100%" in str(r100.json()["detail"])


# ======================================== REQ-007 · Costeo de paquetes

def _crear_paquete(client, admin, nombre, productos, ganancia):
    import json
    r = client.post("/api/paquetes", headers=admin, data={
        "nombre": nombre, "porcentaje_ganancia": ganancia,
        "productos_json": json.dumps([{"producto_id": p, "cantidad": c} for p, c in productos])})
    assert r.status_code == 200, r.text
    return client.get(f"/api/paquetes/{r.json()['id']}", headers=admin).json()


def test_TC014_paquete_calcula_costo_y_precio(client, admin, db):
    """TC-014 · CA-014 · T11 — Pie de Limón + Alfajores x6 con 50 %."""
    paq = _crear_paquete(client, admin, "Pack TC-014",
                         [(_producto(db, "Pie de Limon").id, 1), (_producto(db, "Alfajores x6").id, 1)], 50)
    assert paq["precio_costo_real"] == pytest.approx(12.02)
    assert paq["precio_referencia_suma"] == pytest.approx(27.00)
    assert paq["precio_venta"] == pytest.approx(24.50)


def test_TC015_paquete_un_producto_multiplica_por_cantidad(client, admin, db):
    """TC-015 · CA-015 · T03 — Torta de Chocolate × 3 con 50 %."""
    paq = _crear_paquete(client, admin, "Pack TC-015", [(_producto(db, "Torta de Chocolate").id, 3)], 50)
    assert paq["precio_costo_real"] == pytest.approx(28.59)
    assert paq["precio_referencia_suma"] == pytest.approx(71.70)
    assert paq["precio_venta"] == pytest.approx(57.50)


# ============================================ REQ-008 · Promociones

def test_TC016_promocion_dentro_del_rango_es_activa(client, admin, db):
    """TC-016 · CA-016 · T15 — promoción vigente: activa_ahora = true y precio 20.32."""
    hoy = datetime.now()
    pid = _crear_promocion(client, admin, "Promo TC-016", "producto", _producto(db, "Torta de Chocolate").id, 15,
                           (hoy - timedelta(days=1)).isoformat(timespec="seconds"),
                           (hoy + timedelta(days=7)).isoformat(timespec="seconds"))
    p = client.get(f"/api/promociones/{pid}", headers=admin).json()
    assert p["activa_ahora"] is True
    assert p["precio_promocion"] == pytest.approx(20.32)


def test_TC017_promocion_vencida_es_inactiva(client, admin, db):
    """TC-017 · CA-017 · T15 — promoción de septiembre: activo = true pero activa_ahora = false."""
    pid = _crear_promocion(client, admin, "Promo TC-017", "producto", _producto(db, "Pie de Limon").id, 10,
                           "2026-09-01T00:00:00", "2026-09-30T23:59:59")
    p = client.get(f"/api/promociones/{pid}", headers=admin).json()
    assert p["activo"] is True and p["activa_ahora"] is False
    activas = client.get("/api/promociones", params={"solo_activas": True}, headers=admin).json()
    assert pid not in [x["id"] for x in activas]


def test_TC040_no_se_vende_promocion_vencida(client, admin, vendedor, db):
    """TC-040 · T14 — vender por API una promoción vencida debe rechazarse."""
    pid = _crear_promocion(client, admin, "Promo TC-017", "producto", _producto(db, "Pie de Limon").id, 10,
                           "2026-09-01T00:00:00", "2026-09-30T23:59:59")
    antes = db.query(Venta).count()
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "promocion", "item_id": pid, "cantidad": 1}])
    assert 400 <= r.status_code < 500, f"respondió {r.status_code}: {r.text}"
    assert "vigente" in str(r.json()["detail"]).lower()
    db.rollback()  # nueva transacción: ver lo que la API ya confirmó
    assert db.query(Venta).count() == antes


def test_TC052_venta_de_promocion_descuenta_stock(client, admin, vendedor, db):
    """TC-052 · T16 — vender una promoción vigente de un producto descuenta los insumos
    de ese producto (caso nuevo, derivado de la ejecución del TC10)."""
    hoy = datetime.now()
    pid = _crear_promocion(client, admin, "Promo Torta", "producto", _producto(db, "Torta de Chocolate").id, 10,
                           (hoy - timedelta(days=1)).isoformat(timespec="seconds"),
                           (hoy + timedelta(days=1)).isoformat(timespec="seconds"))
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "promocion", "item_id": pid, "cantidad": 1}])
    assert r.status_code == 200, r.text
    assert float(_insumo(db, "Huevos").stock_actual) == 26
    assert float(_insumo(db, "Harina de trigo").stock_actual) == 750


# ================================== REQ-009 · Ventas y descuento de stock

def test_TC018_venta_descuenta_stock_de_insumos(client, vendedor, db):
    """TC-018 · CA-018 · T16 — venta E2E de 1 Torta de Chocolate."""
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}])
    assert r.status_code == 200, r.text
    venta = client.get(f"/api/ventas/{r.json()['id']}", headers=vendedor).json()
    assert venta["total"] == pytest.approx(23.90)
    assert venta["estado_pago"] == "pendiente" and venta["estado_venta"] == "en_proceso"
    esperado = {"Harina de trigo": 750, "Azucar blanca": 800, "Mantequilla": 350, "Huevos": 26,
                "Leche fresca": 800, "Cacao en polvo": 400, "Levadura seca": 90, "Sal": 995}
    for nombre, stock in esperado.items():
        assert float(_insumo(db, nombre).stock_actual) == stock, nombre
    assert sorted(r.json()["alertas_stock"]) == sorted(
        ["Mantequilla (350.0 mg)", "Cacao en polvo (400.0 mg)", "Levadura seca (90.0 mg)"])


def test_TC019_venta_con_stock_exacto_deja_cero(client, admin, vendedor, db):
    """TC-019 · CA-019 · T03 — stock 8 y la venta pide exactamente 8 huevos."""
    prod = _producto_huevos_x4(client, admin, db)
    _poner_stock(client, admin, db, "Huevos", 8)
    r = _vender(client, vendedor, _id_cliente(db, "Carlos", "Ramos Palomino"),
                [{"item_tipo": "producto", "item_id": prod, "cantidad": 2}])
    assert r.status_code == 200, r.text
    assert client.get(f"/api/ventas/{r.json()['id']}", headers=vendedor).json()["total"] == pytest.approx(8.00)
    assert float(_insumo(db, "Huevos").stock_actual) == 0
    assert r.json()["alertas_stock"] == ["Huevos (0.0 unidad)"]


def test_TC020_venta_con_stock_insuficiente_se_rechaza(client, admin, vendedor, db):
    """TC-020 · CA-020 · T30 — hay 5 huevos y se necesitan 8: 422 sin efectos."""
    prod = _producto_huevos_x4(client, admin, db)
    _poner_stock(client, admin, db, "Huevos", 5)
    r = _vender(client, vendedor, _id_cliente(db, "Carlos", "Ramos Palomino"),
                [{"item_tipo": "producto", "item_id": prod, "cantidad": 2}])
    assert r.status_code == 422
    assert r.json()["detail"]["errores"] == ["'Huevos': necesitas 8.00 unidad pero solo hay 5.00 unidad"]
    db.rollback()
    assert db.query(Venta).count() == 0
    assert float(_insumo(db, "Huevos").stock_actual) == 5


def test_TC050_verificar_stock_antes_de_agregar_al_carrito(client, vendedor, db):
    """TC-050 · T01 — GET /api/ventas/verificar-stock responde la disponibilidad
    (caso nuevo, derivado de la ejecución del TC10)."""
    r = client.get("/api/ventas/verificar-stock", headers=vendedor, params={
        "item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1})
    assert r.status_code == 200, r.text
    assert r.json() == {"disponible": True, "errores": []}


def test_TC051_venta_con_cantidad_cero_o_negativa_se_rechaza(client, vendedor, db):
    """TC-051 · T04 — cantidad 0 o negativa en un ítem: 422, sin venta y sin tocar el stock
    (caso nuevo, derivado de la ejecución del TC10)."""
    torta = _producto(db, "Torta de Chocolate").id
    cliente = _id_cliente(db, "Maria", "Quispe Huanca")
    for cantidad in (0, -2):
        r = _vender(client, vendedor, cliente, [{"item_tipo": "producto", "item_id": torta, "cantidad": cantidad}])
        assert r.status_code == 422, f"cantidad {cantidad}: {r.status_code} {r.text}"
    sin_items = _vender(client, vendedor, cliente, [])
    assert sin_items.status_code == 422
    db.rollback()  # nueva transacción: ver lo que la API ya confirmó
    assert db.query(Venta).count() == 0
    assert float(_insumo(db, "Huevos").stock_actual) == 30


# ================================================ REQ-010 · Boleta PDF

def test_TC021_boleta_pdf_se_genera_en_menos_de_2s(client, vendedor, db):
    """TC-021 · CA-021 · T33 — boleta de 1 Torta de Chocolate para Maria Quispe Huanca."""
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}])
    vid = r.json()["id"]
    inicio = time.perf_counter()
    pdf = client.get(f"/api/ventas/{vid}/boleta", headers=vendedor)
    duracion = time.perf_counter() - inicio
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert f"boleta_{vid}.pdf" in pdf.headers["content-disposition"]
    assert duracion < 2.0
    texto = _texto_pdf(pdf.content)
    for esperado in ("BOLETA DE VENTA", f"B001 - {vid:08d}", "MARIA QUISPE HUANCA",
                     "Torta de Chocolate", "20.25", "3.65", "23.90"):
        assert esperado in texto, esperado


def test_TC022_boleta_con_20_items_lista_todas_las_lineas(client, admin, vendedor, db):
    """TC-022 · CA-022 · T34 — 20 productos distintos en una sola boleta."""
    sal = _insumo(db, "Sal").id
    items = []
    for n in range(1, 21):
        pid = _crear_producto(client, admin, f"Prueba boleta {n:02d}", [(sal, 1)], 50)
        items.append({"item_tipo": "producto", "item_id": pid, "cantidad": 1})
    r = _vender(client, vendedor, _id_cliente(db, "Luisa", "Mendoza Torres"), items)
    assert r.status_code == 200, r.text
    venta = client.get(f"/api/ventas/{r.json()['id']}", headers=vendedor).json()
    assert len(venta["items"]) == 20
    assert venta["total"] == pytest.approx(sum(i["subtotal"] for i in venta["items"]))
    texto = _texto_pdf(client.get(f"/api/ventas/{venta['id']}/boleta", headers=vendedor).content)
    for n in range(1, 21):
        assert f"Prueba boleta {n:02d}" in texto
    assert f"{venta['total']:.2f}" in texto


# ======================================= REQ-011 · Google Calendar (entregas)

def test_TC023_venta_con_entrega_crea_evento_en_calendar(client, vendedor, db, monkeypatch):
    """TC-023 · CA-023 · T43 — con cuenta conectada se envía el evento de entrega.
    Google Calendar: doble de prueba que captura el evento enviado (con la cuenta
    real se verifica manualmente en la demo)."""
    from models.calendario import Calendario
    import services.google_calendar as gc
    enviados = []

    class _Servicio:
        def events(self):
            return self

        def insert(self, calendarId, body):
            enviados.append(body)
            return self

        def execute(self):
            return {"id": "evento-prueba"}

    db.add(Calendario(refresh_token="token-de-prueba", cuenta_email="dulcelazo@gmail.com"))
    db.commit()
    monkeypatch.setattr(gc, "get_calendar_service", lambda _rt: _Servicio())

    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}],
                fecha_entrega="2026-10-25T15:00:00", notas="Escribir «Feliz cumpleaños»")
    assert r.status_code == 200, r.text
    entrega = [e for e in enviados if e["summary"].startswith("🧁 Entrega")]
    assert len(entrega) == 1
    ev = entrega[0]
    assert ev["summary"] == "🧁 Entrega — Maria Quispe Huanca"
    assert ev["start"]["dateTime"].startswith("2026-10-25T15:00")
    assert ev["end"]["dateTime"].startswith("2026-10-25T16:00")
    assert f"Entrega de pedido #{r.json()['id']}" in ev["description"]
    assert "Total: S/ 23.90" in ev["description"] and "Feliz cumpleaños" in ev["description"]
    assert ev["reminders"]["overrides"] == [{"method": "popup", "minutes": 60}, {"method": "email", "minutes": 120}]


def test_TC024_venta_sin_google_no_crea_evento(client, vendedor, db, capsys):
    """TC-024 · CA-024 · T44 — sin cuenta conectada la venta con fecha de entrega se registra normal."""
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}],
                fecha_entrega="2026-10-25T15:00:00")
    assert r.status_code == 200, r.text
    venta = client.get(f"/api/ventas/{r.json()['id']}", headers=vendedor).json()
    assert venta["fecha_entrega"].startswith("2026-10-25T15:00")
    assert "[Calendar] Error creando evento venta" not in capsys.readouterr().out


# ============================================ REQ-012 · Direcciones

def test_TC025_primera_direccion_principal(client, vendedor, db):
    """TC-025 · CA-025 · T26 — se agrega la primera dirección de Jorge Vargas como principal."""
    cid = _id_cliente(db, "Jorge", "Vargas Condori")
    r = client.post(f"/api/clientes/{cid}/direcciones", headers=vendedor, json={
        "etiqueta": "casa", "direccion": "Av. Brasil 1450", "distrito": "Pueblo Libre, Lima",
        "referencia": "Frente al parque", "principal": True})
    assert r.status_code == 200, r.text
    dirs = client.get(f"/api/clientes/{cid}/direcciones", headers=vendedor).json()
    assert dirs[0]["direccion"] == "Av. Brasil 1450" and dirs[0]["principal"] is True


def test_TC026_nueva_principal_desmarca_la_anterior(client, vendedor, db):
    """TC-026 · CA-026 · T10 — la nueva dirección principal reemplaza a la anterior."""
    cid = _id_cliente(db, "Jorge", "Vargas Condori")
    client.post(f"/api/clientes/{cid}/direcciones", headers=vendedor, json={
        "etiqueta": "casa", "direccion": "Av. Brasil 1450", "distrito": "Pueblo Libre, Lima", "principal": True})
    client.post(f"/api/clientes/{cid}/direcciones", headers=vendedor, json={
        "etiqueta": "trabajo", "direccion": "Jr. de la Unión 500", "distrito": "Cercado de Lima", "principal": True})
    dirs = client.get(f"/api/clientes/{cid}/direcciones", headers=vendedor).json()
    principales = [d["direccion"] for d in dirs if d["principal"]]
    assert principales == ["Jr. de la Unión 500"]
    assert dirs[0]["direccion"] == "Jr. de la Unión 500"
    assert "Av. Brasil 1450" in [d["direccion"] for d in dirs]


# ======================================= REQ-013 · Pagos a colaboradores

def test_TC027_pago_a_colaborador_aparece_en_historial(client, admin, db):
    """TC-027 · CA-027 · T26 — pago mensual de S/ 1200 a Marco Huanca Lima."""
    col = db.query(Colaborador).filter_by(nombres="Marco", apellidos="Huanca Lima").one()
    r = client.post("/api/finanzas/pagos-colaboradores", headers=admin, json={
        "colaborador_id": col.id, "monto": 1200.00, "periodo": "Octubre 2026", "notas": "Pago mensual"})
    assert r.status_code == 200, r.text
    pagos = client.get("/api/finanzas/pagos-colaboradores", headers=admin).json()
    assert any(p["colaborador_id"] == col.id and float(p["monto"]) == 1200 and p["periodo"] == "Octubre 2026"
               for p in pagos)


def test_TC028_pago_a_colaborador_inexistente_da_404(client, admin):
    """TC-028 · CA-028 · T02 — colaborador 9999 no existe."""
    antes = len(client.get("/api/finanzas/pagos-colaboradores", headers=admin).json())
    r = client.post("/api/finanzas/pagos-colaboradores", headers=admin,
                    json={"colaborador_id": 9999, "monto": 500.00, "periodo": "Octubre 2026"})
    assert r.status_code == 404 and r.json()["detail"] == "Colaborador no encontrado"
    assert len(client.get("/api/finanzas/pagos-colaboradores", headers=admin).json()) == antes


# ============================================ REQ-014 · Reportes financieros

def test_TC029_reporte_ganancia_solo_ventas_pagadas(client, admin, vendedor, db):
    """TC-029 · CA-029 · T11 — la ganancia estimada del mes considera solo ventas pagadas."""
    cli = _id_cliente(db, "Maria", "Quispe Huanca")
    a = _vender(client, vendedor, cli, [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}])
    _vender(client, vendedor, cli, [{"item_tipo": "producto", "item_id": _producto(db, "Alfajores x6").id, "cantidad": 1}])
    client.patch(f"/api/ventas/{a.json()['id']}/marcar-pagado", headers=vendedor)
    hoy = datetime.now()
    resumen = client.get("/api/finanzas/ventas-detalle", headers=admin,
                         params={"mes": hoy.month, "anio": hoy.year}).json()["resumen"]
    assert resumen["ingresos_pagados"] == pytest.approx(23.90)
    assert resumen["ganancia_total"] == pytest.approx(14.37)


def test_TC030_reporte_periodo_vacio_devuelve_ceros(client, admin):
    """TC-030 · CA-030 · T34 — enero 2026 sin movimientos: todo en 0, sin error 500."""
    v = client.get("/api/finanzas/ventas-detalle", headers=admin, params={"mes": 1, "anio": 2026})
    i = client.get("/api/finanzas/insumos", headers=admin, params={"mes": 1, "anio": 2026})
    assert v.status_code == i.status_code == 200
    assert v.json()["ventas"] == [] and v.json()["resumen"]["ganancia_total"] == 0
    assert i.json()["insumos"] == [] and i.json()["total_gasto"] == 0


# ============================================ REQ-015 · Gastos de marketing

@pytest.mark.skip(reason="BLOQUEADO: REQ-015 (gastos de marketing) no está implementado en el sistema")
def test_TC031_indicadores_de_gasto_de_marketing():
    """TC-031 · CA-031 · T11 — bloqueado: no existe el módulo de gastos de marketing."""


@pytest.mark.skip(reason="BLOQUEADO: REQ-015 (gastos de marketing) no está implementado en el sistema")
def test_TC032_marketing_con_cero_contactos_no_divide_entre_cero():
    """TC-032 · CA-032 · T03 — bloqueado: no existe el módulo de gastos de marketing."""


# ============================================== REQ-016 · Sugerencias con IA

def test_TC033_ia_sugiere_promociones(client, admin, db, monkeypatch):
    """TC-033 · CA-033 · T43 — con IA disponible se usan sus porcentajes (no los de respaldo).
    Groq: doble de prueba con una respuesta válida (con la clave real se verifica en la demo)."""
    import json
    import services.groq_service as gs

    class _Resp:
        choices = [type("C", (), {"message": type("M", (), {"content": json.dumps([
            {"nivel": "Oferta Suave", "porcentaje_descuento": 8, "descripcion": "a"},
            {"nivel": "Oferta Atractiva", "porcentaje_descuento": 18, "descripcion": "b"},
            {"nivel": "Oferta Agresiva", "porcentaje_descuento": 28, "descripcion": "c"}])})()})()]

    class _Cliente:
        chat = type("Chat", (), {"completions": type("Comp", (), {"create": staticmethod(lambda **k: _Resp())})()})()

    monkeypatch.setattr(gs, "_get_client", lambda: _Cliente())
    pid = _producto(db, "Torta de Chocolate").id
    r = client.get(f"/api/promociones/sugerir-ia/producto/{pid}", headers=admin)
    assert r.status_code == 200, r.text
    s = r.json()
    if isinstance(s, dict):
        s = s.get("sugerencias", s)
    pcts = [x["porcentaje_descuento"] for x in s]
    assert pcts == [8, 18, 28]
    assert s[0]["precio_promocion"] == pytest.approx(round(23.90 * 0.92, 2))


def test_TC034_ia_sin_clave_devuelve_respaldo(client, admin, db):
    """TC-034 · CA-034 · T44 — sin GROQ_API_KEY se devuelven las 3 sugerencias locales."""
    pid = _producto(db, "Torta de Chocolate").id
    r = client.get(f"/api/promociones/sugerir-ia/producto/{pid}", headers=admin)
    assert r.status_code == 200, r.text
    s = r.json()
    if isinstance(s, dict):
        s = s.get("sugerencias", s)
    assert [(x["nivel"], x["porcentaje_descuento"], x["precio_promocion"], x["margen_restante"]) for x in s] == [
        ("Oferta Suave", 7, 22.23, 57.1), ("Oferta Atractiva", 17, 19.84, 52.0), ("Oferta Agresiva", 30, 16.73, 43.0)]


# ================================================= REQ-017 · Empresa

def test_TC035_crear_datos_de_empresa(client, admin, db):
    """TC-035 · CA-035 · T26 — con la tabla empresa vacía, guardar crea un único registro."""
    db.query(Empresa).delete()
    db.commit()
    assert client.get("/api/empresa", headers=admin).json() == {}
    r = client.put("/api/empresa", headers=admin, json={
        "nombre": "Dulce Lazo E.I.R.L.", "ruc": "20123456789", "numero_yape_plin": "987654321",
        "direccion": "Av. Ejemplo 123", "distrito": "San Isidro, Lima"})
    assert r.status_code == 200
    assert client.get("/api/empresa", headers=admin).json()["ruc"] == "20123456789"
    db.rollback()  # nueva transacción: ver lo que la API ya confirmó
    assert db.query(Empresa).count() == 1


def test_TC036_actualizar_empresa_no_duplica(client, admin, vendedor, db):
    """TC-036 · CA-036 · T28 — actualizar mantiene un solo registro y la boleta usa el nuevo nombre."""
    id_antes = client.get("/api/empresa", headers=admin).json()["id"]
    client.put("/api/empresa", headers=admin, json={
        "nombre": "Dulce Lazo S.A.C.", "telefono": "01-234-5678", "nro_cuenta_banco": "0011-0111-0200123456"})
    emp = client.get("/api/empresa", headers=admin).json()
    assert emp["id"] == id_antes and emp["nombre"] == "Dulce Lazo S.A.C."
    db.rollback()  # nueva transacción: ver lo que la API ya confirmó
    assert db.query(Empresa).count() == 1
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}])
    texto = _texto_pdf(client.get(f"/api/ventas/{r.json()['id']}/boleta", headers=vendedor).content)
    assert "DULCE LAZO S.A.C." in texto


# ================================================== Transversal · humo

def test_TC037_smoke_api_login_modulos_y_venta(client, admin, vendedor, db):
    """TC-037 · T45 — la API responde, los módulos cargan y se puede vender."""
    assert client.get("/").json() == {"mensaje": "API Dulce Lazo funcionando correctamente"}
    for ruta in ("/api/productos", "/api/paquetes", "/api/promociones", "/api/clientes", "/api/ventas"):
        assert client.get(ruta, headers=vendedor).status_code == 200, ruta
    for ruta in ("/api/insumos", "/api/colaboradores", "/api/finanzas/dashboard", "/api/auth/usuarios", "/api/empresa"):
        assert client.get(ruta, headers=admin).status_code == 200, ruta
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}])
    assert r.status_code == 200


# ======================================== REQ-018 · Reabastecimiento

def _insumo_de_prueba(client, admin, nombre, cantidad, precio):
    r = client.post("/api/insumos", headers=admin, json={
        "nombre": nombre, "unidad": "unidad", "cantidad_compra": cantidad, "precio_compra": precio})
    assert r.status_code == 200, r.text
    return r.json()["insumo"]["id"]


def test_TC041_reabastecimiento_calcula_precio_promedio(client, admin):
    """TC-041 · CA-037 · T26 — stock 10 a S/ 2.50 + compra de 5 por S/ 15 → 15 a S/ 2.67."""
    iid = _insumo_de_prueba(client, admin, "Harina TC-041", 10, 25.00)
    r = client.post(f"/api/insumos/{iid}/reabastecer", headers=admin,
                    json={"cantidad_compra": 5, "precio_compra": 15.00})
    assert r.status_code == 200, r.text
    assert r.json()["insumo"]["stock_actual"] == 15
    assert round(r.json()["insumo"]["precio_unitario"], 2) == 2.67


def test_TC042_reabastecimiento_desde_stock_cero(client, admin):
    """TC-042 · CA-038 · T03 — insumo en 0 y precio 0 + compra de 10 por S/ 25 → precio 2.50."""
    iid = _insumo_de_prueba(client, admin, "Prueba stock cero", 1, 1.00)
    client.put(f"/api/insumos/{iid}", headers=admin, json={"stock_actual": 0, "precio_unitario": 0})
    r = client.post(f"/api/insumos/{iid}/reabastecer", headers=admin,
                    json={"cantidad_compra": 10, "precio_compra": 25.00})
    assert r.status_code == 200, r.text
    assert r.json()["insumo"]["stock_actual"] == 10
    assert r.json()["insumo"]["precio_unitario"] == pytest.approx(2.50)


def test_TC043_reabastecimiento_con_datos_invalidos(client, admin):
    """TC-043 · CA-039 · T04 — cantidad 0 o precio negativo → 400, el stock no cambia."""
    iid = _insumo_de_prueba(client, admin, "Insumo TC-043", 10, 25.00)
    r1 = client.post(f"/api/insumos/{iid}/reabastecer", headers=admin, json={"cantidad_compra": 0, "precio_compra": 10})
    r2 = client.post(f"/api/insumos/{iid}/reabastecer", headers=admin, json={"cantidad_compra": 5, "precio_compra": -1})
    assert r1.status_code == r2.status_code == 400
    assert client.get(f"/api/insumos/{iid}", headers=admin).json()["stock_actual"] == 10


# ======================================== REQ-019 · Gestión de usuarios

def test_TC044_admin_crea_usuario_vendedor(client, admin, db):
    """TC-044 · CA-040 · T26 — alta de María Rojas como vendedora; puede iniciar sesión."""
    r = client.post("/api/auth/usuarios", headers=admin, json={
        "nombres": "María", "apellidos": "Rojas", "correo": "mrojas@dulcelazo.pe",
        "password": "Vendedora123", "rol": "vendedor"})
    assert r.status_code == 200, r.text
    lista = client.get("/api/auth/usuarios", headers=admin).json()
    assert any(u["correo"] == "mrojas@dulcelazo.pe" and u["rol"] == "vendedor" for u in lista)
    login = client.post("/api/auth/login", data={"username": "mrojas@dulcelazo.pe", "password": "Vendedora123"})
    assert login.status_code == 200
    db.rollback()
    guardado = db.query(Usuario).filter_by(correo="mrojas@dulcelazo.pe").one().hashed_password
    assert guardado.startswith("$2b$") and "Vendedora123" not in guardado


def test_TC045_usuario_con_correo_duplicado_da_400(client, admin, db):
    """TC-045 · CA-041 · T30 — no se puede registrar dos veces admin@dulcelazo.pe."""
    r = client.post("/api/auth/usuarios", headers=admin, json={
        "nombres": "Otro", "apellidos": "Admin", "correo": ADMIN[0], "password": "Otra1234", "rol": "admin"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Ya existe un usuario con ese correo"
    db.rollback()
    assert db.query(Usuario).filter_by(correo=ADMIN[0]).count() == 1


def test_TC046_login_con_cuenta_desactivada_da_401(client, admin, db):
    """TC-046 · CA-042 · T14 — una cuenta desactivada no puede iniciar sesión."""
    client.post("/api/auth/usuarios", headers=admin, json={
        "nombres": "Vendedor", "apellidos": "Dos", "correo": "vendedor2@dulcelazo.pe",
        "password": "Vendedor123", "rol": "vendedor"})
    db.rollback()
    uid = db.query(Usuario).filter_by(correo="vendedor2@dulcelazo.pe").one().id
    client.put(f"/api/auth/usuarios/{uid}", headers=admin, json={"activo": False})
    r = client.post("/api/auth/login", data={"username": "vendedor2@dulcelazo.pe", "password": "Vendedor123"})
    assert r.status_code == 401
    assert "access_token" not in r.json()


def test_TC049_registro_de_usuario_rechaza_datos_invalidos(client, admin, db):
    """TC-049 · T02 — el alta de usuario valida formato de nombre, correo y contraseña
    (caso nuevo, trazado a los 30 fallos de las pruebas unitarias del TC7)."""
    invalidos = [
        {"nombres": "Juan3", "apellidos": "Pérez", "correo": "juan3@dulcelazo.pe", "password": "Password123"},
        {"nombres": "Juan", "apellidos": "Pérez", "correo": "juan.perez.dulcelazo.pe", "password": "Password123"},
        {"nombres": "Juan", "apellidos": "Pérez", "correo": "juan@dulcelazo.pe", "password": "12345678"},
        {"nombres": "   ", "apellidos": "Pérez", "correo": "vacio@dulcelazo.pe", "password": "Password123"},
    ]
    for datos in invalidos:
        r = client.post("/api/auth/usuarios", headers=admin, json=datos)
        assert r.status_code == 422, f"{datos} → {r.status_code}"
    db.rollback()  # nueva transacción: ver lo que la API ya confirmó
    assert db.query(Usuario).count() == 2  # solo admin y vendedor de la precondición


# ============================================ REQ-020 · Estados de venta

def _venta_de_prueba(client, vendedor, db):
    r = _vender(client, vendedor, _id_cliente(db, "Maria", "Quispe Huanca"),
                [{"item_tipo": "producto", "item_id": _producto(db, "Torta de Chocolate").id, "cantidad": 1}])
    return r.json()["id"]


def test_TC047_venta_ciclo_de_estados_valido(client, admin, vendedor, db):
    """TC-047 · CA-043 · T28 — en_proceso → completada y pago pendiente → pagado."""
    vid = _venta_de_prueba(client, vendedor, db)
    assert client.patch(f"/api/ventas/{vid}/estado", params={"estado": "completada"}, headers=admin).status_code == 200
    assert client.patch(f"/api/ventas/{vid}/marcar-pagado", headers=admin).status_code == 200
    v = client.get(f"/api/ventas/{vid}", headers=admin).json()
    assert v["estado_venta"] == "completada" and v["estado_pago"] == "pagado"


def test_TC048_venta_estado_invalido_da_400(client, admin, vendedor, db):
    """TC-048 · CA-044 · T11 — «entregado» no es un estado válido."""
    vid = _venta_de_prueba(client, vendedor, db)
    r = client.patch(f"/api/ventas/{vid}/estado", params={"estado": "entregado"}, headers=admin)
    assert r.status_code == 400 and r.json()["detail"] == "Estado inválido"
    assert client.get(f"/api/ventas/{vid}", headers=admin).json()["estado_venta"] == "en_proceso"
