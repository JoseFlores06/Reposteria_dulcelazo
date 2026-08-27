from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from database import get_db
from models.venta import Venta, VentaItem, MetodoPago, EstadoPago, EstadoVenta, ItemTipoVenta
from models.cliente import Cliente
from models.usuario import Usuario
from models.producto import Producto, ProductoInsumo
from models.paquete import Paquete
from models.promocion import Promocion
from auth import requerir_autenticado, requerir_admin, obtener_usuario_actual
from services.pdf_service import generar_boleta_pdf
from services.stock_service import verificar_stock, descontar_stock, insumos_stock_bajo
from services.google_calendar import crear_evento_stock_bajo, crear_evento_venta, esta_conectado
from utils.timezone import now_lima

router = APIRouter()


class VentaItemCreate(BaseModel):
    item_tipo: ItemTipoVenta
    item_id: int
    cantidad: int


class VentaCreate(BaseModel):
    cliente_id: int
    metodo_pago: MetodoPago
    notas: Optional[str] = None
    fecha_entrega: Optional[datetime] = None
    fuente_marketing: Optional[str] = None
    direccion_entrega: Optional[str] = None
    items: List[VentaItemCreate]


def venta_to_dict(v: Venta, incluir_items: bool = False):
    data = {
        "id": v.id,
        "cliente_id": v.cliente_id,
        "cliente_nombre": f"{v.cliente.nombres} {v.cliente.apellidos}" if v.cliente else "Sin cliente",
        "colaborador_id": v.colaborador_id,
        "colaborador_nombre": f"{v.colaborador.nombres} {v.colaborador.apellidos}" if v.colaborador else None,
        "fecha_hora": v.fecha_hora.isoformat() if v.fecha_hora else None,
        "fecha_entrega": v.fecha_entrega.isoformat() if v.fecha_entrega else None,
        "metodo_pago": v.metodo_pago,
        "estado_pago": v.estado_pago,
        "estado_venta": v.estado_venta,
        "subtotal": float(v.subtotal),
        "total": float(v.total),
        "notas": v.notas,
        "fuente_marketing": v.fuente_marketing,
        "direccion_entrega": v.direccion_entrega,
    }
    if incluir_items:
        data["items"] = [
            {
                "id": item.id,
                "item_tipo": item.item_tipo,
                "item_id": item.item_id,
                "nombre_snapshot": item.nombre_snapshot,
                "precio_unitario_snapshot": float(item.precio_unitario_snapshot),
                "cantidad": item.cantidad,
                "subtotal": float(item.subtotal),
            }
            for item in v.items
        ]
    return data


def obtener_precio_item(db: Session, item_tipo: str, item_id: int):
    if item_tipo == "producto":
        obj = db.query(Producto).filter(Producto.id == item_id, Producto.activo == True).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Producto {item_id} no encontrado o inactivo")
        return obj.nombre, obj.precio_venta
    elif item_tipo == "paquete":
        obj = db.query(Paquete).filter(Paquete.id == item_id, Paquete.activo == True).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Paquete {item_id} no encontrado o inactivo")
        return obj.nombre, obj.precio_venta
    elif item_tipo == "promocion":
        obj = db.query(Promocion).filter(Promocion.id == item_id, Promocion.activo == True).first()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Promoción {item_id} no encontrada o inactiva")
        return obj.nombre, obj.precio_promocion
    raise HTTPException(status_code=400, detail="Tipo de item inválido")


@router.get("")
def listar_ventas(
    orden: str = "desc",
    estado_pago: Optional[str] = None,
    estado_venta: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado),
):
    query = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.colaborador),
        joinedload(Venta.items),
    )
    if estado_pago:
        query = query.filter(Venta.estado_pago == estado_pago)
    if estado_venta:
        query = query.filter(Venta.estado_venta == estado_venta)
    if orden == "asc":
        query = query.order_by(Venta.fecha_hora.asc())
    else:
        query = query.order_by(Venta.fecha_hora.desc())
    return [venta_to_dict(v, incluir_items=True) for v in query.all()]


@router.get("/{venta_id}")
def obtener_venta(venta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    v = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.colaborador),
        joinedload(Venta.items),
    ).filter(Venta.id == venta_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta_to_dict(v, incluir_items=True)


@router.get("/verificar-stock")
def verificar_stock_pedido(
    item_tipo: str,
    item_id: int,
    cantidad: int = 1,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado),
):
    """Verifica si hay suficiente stock para un item antes de agregar al carrito."""
    errores = verificar_stock(db, item_tipo, item_id, cantidad)
    return {"disponible": len(errores) == 0, "errores": errores}


@router.post("")
def crear_venta(
    data: VentaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # 1. Verificar stock antes de crear la venta
    errores_stock: list[str] = []
    for item_data in data.items:
        if item_data.item_tipo in ("producto", "paquete"):
            errs = verificar_stock(db, item_data.item_tipo, item_data.item_id, item_data.cantidad)
            errores_stock.extend(errs)

    if errores_stock:
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "stock_insuficiente",
                "mensaje": "No hay suficiente stock para preparar este pedido",
                "errores": errores_stock,
            },
        )

    # 2. Crear la venta
    venta = Venta(
        cliente_id=data.cliente_id,
        colaborador_id=usuario.id,
        metodo_pago=data.metodo_pago,
        estado_pago=EstadoPago.pendiente,
        estado_venta=EstadoVenta.en_proceso,
        notas=data.notas,
        fecha_entrega=data.fecha_entrega,
        fecha_hora=now_lima(),
        fuente_marketing=data.fuente_marketing,
        direccion_entrega=data.direccion_entrega,
        subtotal=Decimal("0"),
        total=Decimal("0"),
    )
    db.add(venta)
    db.flush()

    total = Decimal("0")
    for item_data in data.items:
        nombre, precio_unitario = obtener_precio_item(db, item_data.item_tipo, item_data.item_id)
        subtotal_item = precio_unitario * item_data.cantidad
        total += subtotal_item

        item = VentaItem(
            venta_id=venta.id,
            item_tipo=item_data.item_tipo,
            item_id=item_data.item_id,
            nombre_snapshot=nombre,
            precio_unitario_snapshot=precio_unitario,
            cantidad=item_data.cantidad,
            subtotal=subtotal_item,
        )
        db.add(item)

    venta.subtotal = total
    venta.total = total

    # 3. Descontar stock
    insumos_bajos: list = []
    for item_data in data.items:
        if item_data.item_tipo in ("producto", "paquete"):
            bajos = descontar_stock(db, item_data.item_tipo, item_data.item_id, item_data.cantidad)
            insumos_bajos.extend(bajos)

    # Eliminar duplicados por id
    seen_ids = set()
    insumos_bajos_uniq = []
    for ins in insumos_bajos:
        if ins.id not in seen_ids:
            seen_ids.add(ins.id)
            insumos_bajos_uniq.append(ins)

    db.commit()
    db.refresh(venta)

    # 4. Crear eventos en Google Calendar (post-commit)
    alertas: list[str] = []
    if insumos_bajos_uniq:
        names = [f"{i.nombre} ({float(i.stock_actual):.1f} {i.unidad})" for i in insumos_bajos_uniq]
        alertas = names
        crear_evento_stock_bajo(db, insumos_bajos_uniq)

    if data.fecha_entrega:
        crear_evento_venta(db, venta, data.fecha_entrega)

    respuesta = {
        "mensaje": "Venta registrada correctamente",
        "id": venta.id,
        "alertas_stock": alertas,
    }
    return respuesta


@router.patch("/{venta_id}/marcar-pagado")
def marcar_pagado(venta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    venta.estado_pago = EstadoPago.pagado
    db.commit()
    return {"mensaje": "Venta marcada como pagada"}


@router.patch("/{venta_id}/estado")
def cambiar_estado_venta(
    venta_id: int,
    estado: str,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado),
):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    try:
        venta.estado_venta = EstadoVenta(estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="Estado inválido")
    db.commit()
    return {"mensaje": f"Estado actualizado a {estado}"}


@router.get("/{venta_id}/boleta")
def descargar_boleta(venta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    v = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.colaborador),
        joinedload(Venta.items),
    ).filter(Venta.id == venta_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    from models.empresa import Empresa
    empresa = db.query(Empresa).first()

    pdf_bytes = generar_boleta_pdf(v, empresa)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=boleta_{venta_id}.pdf"},
    )
