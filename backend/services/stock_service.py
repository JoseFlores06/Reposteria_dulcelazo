"""
Servicio de control de stock de insumos.
- Verifica disponibilidad antes de registrar ventas
- Descuenta stock al confirmar la venta
- Detecta insumos con stock bajo
"""
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload

from models.insumo import Insumo
from models.producto import Producto, ProductoInsumo
from models.paquete import Paquete, PaqueteProducto

# Umbrales de stock bajo
UMBRAL_BAJO = {
    "ml":     Decimal("500"),
    "mg":     Decimal("500"),
    "unidad": Decimal("4"),
}


def umbral_para(unidad: str) -> Decimal:
    return UMBRAL_BAJO.get(unidad, Decimal("4"))


def stock_es_bajo(insumo: Insumo) -> bool:
    return Decimal(str(insumo.stock_actual)) < umbral_para(insumo.unidad)


def _insumos_de_producto(db: Session, producto_id: int) -> list[tuple[Insumo, Decimal]]:
    """Devuelve [(insumo, cantidad_necesaria_unitaria), ...]"""
    pis = (
        db.query(ProductoInsumo)
        .filter(ProductoInsumo.producto_id == producto_id)
        .join(ProductoInsumo.insumo)
        .all()
    )
    return [(pi.insumo, Decimal(str(pi.cantidad_necesaria))) for pi in pis]


def _insumos_de_paquete(db: Session, paquete_id: int) -> list[tuple[Insumo, Decimal]]:
    """Suma insumos de todos los productos del paquete (por cantidades del paquete)."""
    pps = (
        db.query(PaqueteProducto)
        .filter(PaqueteProducto.paquete_id == paquete_id)
        .options(joinedload(PaqueteProducto.producto).joinedload(Producto.insumos).joinedload(ProductoInsumo.insumo))
        .all()
    )
    acum: dict[int, tuple[Insumo, Decimal]] = {}
    for pp in pps:
        cant_prod = Decimal(str(pp.cantidad))
        for pi in pp.producto.insumos:
            insumo = pi.insumo
            cant_total = Decimal(str(pi.cantidad_necesaria)) * cant_prod
            if insumo.id in acum:
                acum[insumo.id] = (insumo, acum[insumo.id][1] + cant_total)
            else:
                acum[insumo.id] = (insumo, cant_total)
    return list(acum.values())


def _resolver_item(db: Session, item_tipo: str, item_id: int) -> tuple[str | None, int | None]:
    """Una promoción consume los insumos del producto o paquete al que está ligada
    (DEF-DL-011: antes vender una promoción no descontaba ningún insumo)."""
    item_tipo = getattr(item_tipo, "value", item_tipo)
    if item_tipo == "promocion":
        from services.promocion_service import item_de_promocion
        return item_de_promocion(db, item_id)
    return item_tipo, item_id


def requerimientos_pedido(db: Session, items) -> list[tuple[Insumo, Decimal]]:
    """Suma lo que necesita TODO el pedido por insumo, aunque varios ítems usen el
    mismo insumo. items = objetos/dicts con item_tipo, item_id y cantidad."""
    acum: dict[int, tuple[Insumo, Decimal]] = {}
    for it in items:
        tipo = it["item_tipo"] if isinstance(it, dict) else it.item_tipo
        iid = it["item_id"] if isinstance(it, dict) else it.item_id
        cant = Decimal(str(it["cantidad"] if isinstance(it, dict) else it.cantidad))
        tipo, iid = _resolver_item(db, tipo, iid)
        if tipo == "producto":
            pares = _insumos_de_producto(db, iid)
        elif tipo == "paquete":
            pares = _insumos_de_paquete(db, iid)
        else:
            continue
        for insumo, cant_unit in pares:
            previo = acum.get(insumo.id, (insumo, Decimal("0")))[1]
            acum[insumo.id] = (insumo, previo + cant_unit * cant)
    return list(acum.values())


def verificar_pedido(db: Session, items) -> list[str]:
    """Errores de stock del pedido completo. Lista vacía = se puede preparar."""
    errores = []
    for insumo, necesario in requerimientos_pedido(db, items):
        disponible = Decimal(str(insumo.stock_actual))
        if disponible < necesario:
            errores.append(
                f"'{insumo.nombre}': necesitas {float(necesario):.2f} {insumo.unidad} "
                f"pero solo hay {float(disponible):.2f} {insumo.unidad}"
            )
    return errores


def descontar_pedido(db: Session, items) -> list[Insumo]:
    """Descuenta el stock del pedido completo y devuelve los insumos que quedaron bajos."""
    bajos = []
    for insumo, necesario in requerimientos_pedido(db, items):
        insumo.stock_actual = Decimal(str(insumo.stock_actual)) - necesario
        insumo.comprado = True
        if stock_es_bajo(insumo):
            bajos.append(insumo)
    return bajos


def verificar_stock(
    db: Session,
    item_tipo: str,
    item_id: int,
    cantidad_items: int,
) -> list[str]:
    """
    Verifica si hay suficiente stock para preparar `cantidad_items` de un item.
    Devuelve lista de mensajes de error. Lista vacía = OK.
    """
    errores: list[str] = []
    cant = Decimal(str(cantidad_items))
    item_tipo, item_id = _resolver_item(db, item_tipo, item_id)

    if item_tipo == "producto":
        pares = _insumos_de_producto(db, item_id)
    elif item_tipo == "paquete":
        pares = _insumos_de_paquete(db, item_id)
    else:
        return []  # promocion → no descontamos insumos directamente

    for insumo, cant_unit in pares:
        necesario = cant_unit * cant
        disponible = Decimal(str(insumo.stock_actual))
        if disponible < necesario:
            errores.append(
                f"'{insumo.nombre}': necesitas {float(necesario):.2f} {insumo.unidad} "
                f"pero solo hay {float(disponible):.2f} {insumo.unidad}"
            )
    return errores


def descontar_stock(
    db: Session,
    item_tipo: str,
    item_id: int,
    cantidad_items: int,
) -> list[Insumo]:
    """
    Descuenta el stock para `cantidad_items` de un item.
    Devuelve lista de insumos que quedaron con stock bajo.
    """
    cant = Decimal(str(cantidad_items))

    if item_tipo == "producto":
        pares = _insumos_de_producto(db, item_id)
    elif item_tipo == "paquete":
        pares = _insumos_de_paquete(db, item_id)
    else:
        return []

    bajos: list[Insumo] = []
    for insumo, cant_unit in pares:
        necesario = cant_unit * cant
        insumo.stock_actual = Decimal(str(insumo.stock_actual)) - necesario
        # Al vender un producto se consumen sus insumos → se consideran comprados
        # (gastados) y deben aparecer en Finanzas aunque no se hubieran marcado antes.
        insumo.comprado = True
        if stock_es_bajo(insumo):
            bajos.append(insumo)

    return bajos


def insumos_stock_bajo(db: Session) -> list[Insumo]:
    """Todos los insumos activos con stock bajo."""
    insumos = db.query(Insumo).filter(Insumo.activo == True).all()
    return [i for i in insumos if stock_es_bajo(i)]
