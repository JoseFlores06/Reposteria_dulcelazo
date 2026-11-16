"""
Casos de prueba funcionales — TC12 (Refactorización + REQ-015 Gastos de Marketing).

TC-053  DEF-DL-013: verificar-stock rechaza cantidad=0
TC-054  DEF-DL-013: verificar-stock rechaza cantidad negativa
TC-055  DEF-DL-012: venta concurrente no hace sobreventa (SELECT FOR UPDATE)
TC-056  REQ-015: crear gasto de marketing y listarlo
TC-057  REQ-015: actualizar y eliminar gasto de marketing (solo admin)
"""
import threading

import pytest

from models.insumo import Insumo

ADMIN = ("admin@dulcelazo.pe", "Admin12345!")


# ─────────────────────────── helpers locales ─────────────────────────────────

def _insumo_por_nombre(db, nombre):
    db.rollback()
    return db.query(Insumo).filter_by(nombre=nombre).one()


def _poner_stock(client, admin, db, nombre, stock):
    ins = _insumo_por_nombre(db, nombre)
    r = client.put(f"/api/insumos/{ins.id}", json={"stock_actual": stock}, headers=admin)
    assert r.status_code == 200, r.text


def _id_cliente_1(db):
    from models.cliente import Cliente
    return db.query(Cliente).first().id


def _id_producto_con_harina(client, admin, db):
    """Crea un producto que usa 100 g de harina."""
    harina_id = _insumo_por_nombre(db, "Harina de trigo").id
    import json
    r = client.post("/api/productos", headers=admin, data={
        "nombre": "PanPrueba", "porcentaje_ganancia": "50",
        "insumos_json": json.dumps([{"insumo_id": harina_id, "cantidad_necesaria": 100}]),
    })
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ═══════════════════════════════ DEF-DL-013 ══════════════════════════════════

def test_TC053_verificar_stock_rechaza_cantidad_cero(client, admin, db):
    """TC-053 — verificar-stock rechaza cantidad=0 con 422."""
    prod_id = _id_producto_con_harina(client, admin, db)
    r = client.get(
        "/api/ventas/verificar-stock",
        params={"item_tipo": "producto", "item_id": prod_id, "cantidad": 0},
        headers=admin,
    )
    assert r.status_code == 422, r.text


def test_TC054_verificar_stock_rechaza_cantidad_negativa(client, admin, db):
    """TC-054 — verificar-stock rechaza cantidad negativa con 422."""
    prod_id = _id_producto_con_harina(client, admin, db)
    r = client.get(
        "/api/ventas/verificar-stock",
        params={"item_tipo": "producto", "item_id": prod_id, "cantidad": -3},
        headers=admin,
    )
    assert r.status_code == 422, r.text


# ═══════════════════════════════ DEF-DL-012 ══════════════════════════════════

def test_TC055_ventas_concurrentes_no_sobreventean(client, admin, db):
    """TC-055 — dos ventas simultáneas al mismo insumo con stock para exactamente 1
    deben resultar en una confirmada y la otra rechazada (no en 2 confirmadas)."""
    prod_id = _id_producto_con_harina(client, admin, db)
    # Stock exacto para 1 venta (100 g de harina)
    _poner_stock(client, admin, db, "Harina de trigo", 100)
    cliente_id = _id_cliente_1(db)

    resultados = []

    def vender():
        r = client.post("/api/ventas", json={
            "cliente_id": cliente_id,
            "metodo_pago": "efectivo",
            "items": [{"item_tipo": "producto", "item_id": prod_id, "cantidad": 1}],
        }, headers=admin)
        resultados.append(r.status_code)

    t1 = threading.Thread(target=vender)
    t2 = threading.Thread(target=vender)
    t1.start(); t2.start()
    t1.join(); t2.join()

    exitosas = resultados.count(200)
    # Con SELECT FOR UPDATE exactamente 1 debe pasar
    assert exitosas == 1, (
        f"Se esperaba 1 venta exitosa; se obtuvieron {exitosas}. "
        f"Resultados HTTP: {resultados}"
    )


# ═══════════════════════════════ REQ-015 ════════════════════════════════════

def test_TC056_crear_y_listar_gastos_marketing(client, admin):
    """TC-056 — crear un gasto de marketing y recuperarlo en el listado."""
    payload = {
        "concepto": "Flyers para feria",
        "canal": "Flyers / Impresión",
        "monto": 150.00,
    }
    r = client.post("/api/gastos-marketing", json=payload, headers=admin)
    assert r.status_code == 200, r.text
    creado = r.json()
    assert creado["concepto"] == "Flyers para feria"
    assert creado["canal"] == "Flyers / Impresión"
    assert creado["monto"] == 150.0

    r2 = client.get("/api/gastos-marketing", headers=admin)
    assert r2.status_code == 200
    ids = [g["id"] for g in r2.json()]
    assert creado["id"] in ids


def test_TC057_actualizar_y_eliminar_gasto_marketing(client, admin, vendedor):
    """TC-057 — solo admin puede editar/eliminar; vendedor recibe 403."""
    # Crear
    r = client.post("/api/gastos-marketing", json={
        "concepto": "Instagram post", "monto": 80.0,
    }, headers=admin)
    assert r.status_code == 200, r.text
    gasto_id = r.json()["id"]

    # Vendedor no puede editar
    r_vend = client.patch(
        f"/api/gastos-marketing/{gasto_id}",
        json={"monto": 999.0},
        headers=vendedor,
    )
    assert r_vend.status_code == 403

    # Admin edita
    r_patch = client.patch(
        f"/api/gastos-marketing/{gasto_id}",
        json={"concepto": "Instagram patrocinado", "monto": 95.0},
        headers=admin,
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["monto"] == 95.0
    assert r_patch.json()["concepto"] == "Instagram patrocinado"

    # Admin elimina
    r_del = client.delete(f"/api/gastos-marketing/{gasto_id}", headers=admin)
    assert r_del.status_code == 200

    # Ya no existe
    r_get = client.get(f"/api/gastos-marketing/{gasto_id}", headers=admin)
    assert r_get.status_code == 404
