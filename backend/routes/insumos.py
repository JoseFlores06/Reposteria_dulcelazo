from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from database import get_db
from models.insumo import Insumo, UnidadInsumo
from models.merma_insumo import MermaInsumo
from models.usuario import Usuario
from auth import requerir_admin, requerir_autenticado
from utils.timezone import now_lima

router = APIRouter()


class InsumoCreate(BaseModel):
    nombre: str
    unidad: UnidadInsumo
    cantidad_compra: Decimal
    precio_compra: Decimal
    comprado: bool = True


class InsumoUpdate(BaseModel):
    nombre: Optional[str] = None
    unidad: Optional[UnidadInsumo] = None
    precio_unitario: Optional[Decimal] = None
    stock_actual: Optional[Decimal] = None
    activo: Optional[bool] = None
    comprado: Optional[bool] = None


class MermaCreate(BaseModel):
    cantidad: Decimal
    motivo: str = "vencido"          # 'vencido' | 'otro'
    detalle: Optional[str] = None    # texto libre cuando motivo = 'otro'


def insumo_to_dict(insumo: Insumo):
    return {
        "id": insumo.id,
        "nombre": insumo.nombre,
        "unidad": insumo.unidad,
        "precio_unitario": float(insumo.precio_unitario),
        "stock_actual": float(insumo.stock_actual),
        "fecha_ingreso": insumo.fecha_ingreso.isoformat() if insumo.fecha_ingreso else None,
        "activo": insumo.activo,
        "comprado": bool(insumo.comprado),
    }


def merma_to_dict(m: MermaInsumo):
    return {
        "id": m.id,
        "insumo_id": m.insumo_id,
        "insumo_nombre": m.insumo.nombre if m.insumo else None,
        "unidad": m.insumo.unidad if m.insumo else None,
        "cantidad": float(m.cantidad),
        "motivo": m.motivo,
        "detalle": m.detalle,
        "fecha": m.fecha.isoformat() if m.fecha else None,
    }


@router.get("")
def listar_insumos(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado)
):
    query = db.query(Insumo)
    if activo is not None:
        query = query.filter(Insumo.activo == activo)
    return [insumo_to_dict(i) for i in query.order_by(Insumo.nombre).all()]


@router.get("/mermas")
def listar_mermas(
    insumo_id: Optional[int] = None,
    limite: int = 50,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado),
):
    """Historial de bajas/mermas de insumos (las más recientes primero)."""
    query = db.query(MermaInsumo).options(joinedload(MermaInsumo.insumo))
    if insumo_id is not None:
        query = query.filter(MermaInsumo.insumo_id == insumo_id)
    mermas = query.order_by(MermaInsumo.fecha.desc()).limit(limite).all()
    return [merma_to_dict(m) for m in mermas]


@router.get("/{insumo_id}")
def obtener_insumo(insumo_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    return insumo_to_dict(insumo)


@router.post("")
def crear_insumo(data: InsumoCreate, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    if data.cantidad_compra <= 0:
        raise HTTPException(status_code=400, detail="La cantidad de compra debe ser mayor a 0")
    if data.precio_compra < 0:
        raise HTTPException(status_code=400, detail="El precio de compra no puede ser negativo")

    precio_unitario = (data.precio_compra / data.cantidad_compra).quantize(Decimal("0.000001"))

    insumo = Insumo(
        nombre=data.nombre,
        unidad=data.unidad,
        precio_unitario=precio_unitario,
        stock_actual=data.cantidad_compra,
        comprado=data.comprado,
    )
    db.add(insumo)
    db.commit()
    db.refresh(insumo)
    return {"mensaje": "Insumo creado correctamente", "insumo": insumo_to_dict(insumo)}


@router.put("/{insumo_id}")
def actualizar_insumo(
    insumo_id: int,
    data: InsumoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    if data.nombre is not None:
        insumo.nombre = data.nombre
    if data.unidad is not None:
        insumo.unidad = data.unidad
    if data.precio_unitario is not None:
        insumo.precio_unitario = data.precio_unitario
    if data.stock_actual is not None:
        insumo.stock_actual = data.stock_actual
    if data.activo is not None:
        insumo.activo = data.activo
    if data.comprado is not None:
        insumo.comprado = data.comprado

    db.commit()
    return {"mensaje": "Insumo actualizado correctamente", "insumo": insumo_to_dict(insumo)}


class InsumoReabastecer(BaseModel):
    cantidad_compra: Decimal
    precio_compra: Decimal


@router.post("/{insumo_id}/reabastecer")
def reabastecer_insumo(
    insumo_id: int,
    data: InsumoReabastecer,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    if data.cantidad_compra <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")
    if data.precio_compra < 0:
        raise HTTPException(status_code=400, detail="El precio no puede ser negativo")

    stock_actual = Decimal(str(insumo.stock_actual))
    precio_actual = Decimal(str(insumo.precio_unitario))
    nuevo_precio_unitario = (data.precio_compra / data.cantidad_compra).quantize(Decimal("0.000001"))
    total_stock = stock_actual + data.cantidad_compra

    if total_stock > 0:
        precio_ponderado = (
            (stock_actual * precio_actual + data.precio_compra) / total_stock
        ).quantize(Decimal("0.000001"))
    else:
        precio_ponderado = nuevo_precio_unitario

    insumo.stock_actual = total_stock
    insumo.precio_unitario = precio_ponderado
    insumo.comprado = True  # reabastecer es una compra real → cuenta en Finanzas
    db.commit()
    return {"mensaje": "Stock actualizado correctamente", "insumo": insumo_to_dict(insumo)}


@router.post("/{insumo_id}/merma")
def registrar_merma(
    insumo_id: int,
    data: MermaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Da de baja una cantidad de stock (vencido, dañado, etc.).
    Reduce el stock SIN modificar el precio del insumo y registra el motivo."""
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    if data.cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad a dar de baja debe ser mayor a 0")

    stock_actual = Decimal(str(insumo.stock_actual))
    if data.cantidad > stock_actual:
        raise HTTPException(
            status_code=400,
            detail=f"No puedes dar de baja {float(data.cantidad):.2f} {insumo.unidad}: solo hay {float(stock_actual):.2f} {insumo.unidad} en stock",
        )

    motivo = data.motivo if data.motivo in ("vencido", "otro") else "otro"
    detalle = (data.detalle or "").strip() or None

    # Reducir stock SIN tocar el precio unitario
    insumo.stock_actual = stock_actual - data.cantidad

    merma = MermaInsumo(
        insumo_id=insumo.id,
        cantidad=data.cantidad,
        motivo=motivo,
        detalle=detalle,
        fecha=now_lima(),
    )
    db.add(merma)
    db.commit()
    db.refresh(insumo)
    db.refresh(merma, ["insumo"])
    return {
        "mensaje": "Baja registrada correctamente",
        "insumo": insumo_to_dict(insumo),
        "merma": merma_to_dict(merma),
    }


@router.delete("/{insumo_id}")
def eliminar_insumo(insumo_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    insumo.activo = False
    db.commit()
    return {"mensaje": "Insumo desactivado correctamente"}
