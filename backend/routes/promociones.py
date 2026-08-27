import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime

from database import get_db
from models.promocion import Promocion, ItemTipoPromocion
from models.producto import Producto
from models.paquete import Paquete
from models.usuario import Usuario
from auth import requerir_admin, requerir_autenticado

router = APIRouter()
UPLOAD_DIR = "uploads"


def redimensionar_imagen(ruta: str):
    try:
        from PIL import Image
        img = Image.open(ruta)
        if img.width > 800 or img.height > 800:
            img.thumbnail((800, 800))
            img.save(ruta)
    except Exception:
        pass


def promocion_to_dict(p: Promocion):
    return {
        "id": p.id,
        "nombre": p.nombre,
        "foto": p.foto,
        "descripcion": p.descripcion,
        "item_tipo": p.item_tipo,
        "item_id": p.item_id,
        "precio_original": float(p.precio_original),
        "precio_promocion": float(p.precio_promocion),
        "porcentaje_descuento": float(p.porcentaje_descuento),
        "activo": p.activo,
        "fecha_inicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
        "fecha_fin": p.fecha_fin.isoformat() if p.fecha_fin else None,
        "creado_en": p.creado_en.isoformat() if p.creado_en else None,
    }


def esta_activa_por_fechas(promo: Promocion) -> bool:
    if promo.fecha_inicio is None and promo.fecha_fin is None:
        return promo.activo
    ahora = datetime.utcnow()
    if promo.fecha_inicio and ahora < promo.fecha_inicio:
        return False
    if promo.fecha_fin and ahora > promo.fecha_fin:
        return False
    return True


@router.get("")
def listar_promociones(
    solo_activas: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado)
):
    query = db.query(Promocion)
    promociones = query.order_by(Promocion.creado_en.desc()).all()
    resultado = []
    for p in promociones:
        d = promocion_to_dict(p)
        d["activa_ahora"] = esta_activa_por_fechas(p)
        if solo_activas is not None and solo_activas != d["activa_ahora"]:
            continue
        resultado.append(d)
    return resultado


@router.get("/{promocion_id}")
def obtener_promocion(promocion_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    p = db.query(Promocion).filter(Promocion.id == promocion_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")
    d = promocion_to_dict(p)
    d["activa_ahora"] = esta_activa_por_fechas(p)
    return d


@router.post("")
async def crear_promocion(
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    item_tipo: str = Form(...),
    item_id: int = Form(...),
    porcentaje_descuento: float = Form(...),
    activo: bool = Form(True),
    fecha_inicio: Optional[str] = Form(None),
    fecha_fin: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    # Obtener precio original
    if item_tipo == "producto":
        item = db.query(Producto).filter(Producto.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        precio_original = item.precio_venta
    else:
        item = db.query(Paquete).filter(Paquete.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Paquete no encontrado")
        precio_original = item.precio_venta

    descuento = Decimal(str(porcentaje_descuento))
    precio_promocion = precio_original * (1 - descuento / 100)
    precio_promocion = precio_promocion.quantize(Decimal("0.01"))

    foto_path = None
    if foto and foto.filename:
        ext = foto.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        ruta = os.path.join(UPLOAD_DIR, filename)
        with open(ruta, "wb") as f:
            f.write(await foto.read())
        redimensionar_imagen(ruta)
        foto_path = f"/uploads/{filename}"

    promo = Promocion(
        nombre=nombre,
        foto=foto_path,
        descripcion=descripcion,
        item_tipo=item_tipo,
        item_id=item_id,
        precio_original=precio_original,
        precio_promocion=precio_promocion,
        porcentaje_descuento=descuento,
        activo=activo,
        fecha_inicio=datetime.fromisoformat(fecha_inicio) if fecha_inicio else None,
        fecha_fin=datetime.fromisoformat(fecha_fin) if fecha_fin else None,
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return {"mensaje": "Promoción creada correctamente", "id": promo.id}


@router.put("/{promocion_id}")
async def actualizar_promocion(
    promocion_id: int,
    nombre: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    porcentaje_descuento: Optional[float] = Form(None),
    activo: Optional[bool] = Form(None),
    fecha_inicio: Optional[str] = Form(None),
    fecha_fin: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    promo = db.query(Promocion).filter(Promocion.id == promocion_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")

    if foto and foto.filename:
        ext = foto.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        ruta = os.path.join(UPLOAD_DIR, filename)
        with open(ruta, "wb") as f:
            f.write(await foto.read())
        redimensionar_imagen(ruta)
        promo.foto = f"/uploads/{filename}"

    if nombre is not None:
        promo.nombre = nombre
    if descripcion is not None:
        promo.descripcion = descripcion
    if activo is not None:
        promo.activo = activo
    if fecha_inicio is not None:
        promo.fecha_inicio = datetime.fromisoformat(fecha_inicio) if fecha_inicio else None
    if fecha_fin is not None:
        promo.fecha_fin = datetime.fromisoformat(fecha_fin) if fecha_fin else None

    if porcentaje_descuento is not None:
        descuento = Decimal(str(porcentaje_descuento))
        promo.porcentaje_descuento = descuento
        promo.precio_promocion = (promo.precio_original * (1 - descuento / 100)).quantize(Decimal("0.01"))

    db.commit()
    return {"mensaje": "Promoción actualizada correctamente"}


@router.patch("/{promocion_id}/toggle")
def toggle_promocion(promocion_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    promo = db.query(Promocion).filter(Promocion.id == promocion_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")
    promo.activo = not promo.activo
    db.commit()
    return {"activo": promo.activo}


@router.get("/sugerir-ia/{item_tipo}/{item_id}")
def sugerir_con_ia(
    item_tipo: str,
    item_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    from services.groq_service import sugerir_promociones

    if item_tipo == "producto":
        item = db.query(Producto).filter(Producto.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        precio_original = float(item.precio_venta) if item.precio_venta else 0
        costo_real = float(item.precio_costo) if item.precio_costo else 0
        nombre = item.nombre
    elif item_tipo == "paquete":
        item = db.query(Paquete).filter(Paquete.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Paquete no encontrado")
        precio_original = float(item.precio_venta) if item.precio_venta else 0
        costo_real = float(item.precio_costo_real) if item.precio_costo_real else 0
        nombre = item.nombre
    else:
        raise HTTPException(status_code=400, detail="Tipo de item inválido")

    sugerencias = sugerir_promociones(nombre, precio_original, costo_real)
    return {"sugerencias": sugerencias}


@router.delete("/{promocion_id}")
def eliminar_promocion(promocion_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    promo = db.query(Promocion).filter(Promocion.id == promocion_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")
    db.delete(promo)
    db.commit()
    return {"mensaje": "Promoción eliminada correctamente"}
