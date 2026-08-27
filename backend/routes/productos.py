import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

from database import get_db
from models.producto import Producto, ProductoInsumo, UnidadTiempo
from models.insumo import Insumo
from models.usuario import Usuario
from auth import requerir_admin, requerir_autenticado
from services.costeo import calcular_costo_producto, calcular_precio_venta

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


def producto_to_dict(p: Producto, incluir_insumos: bool = False):
    data = {
        "id": p.id,
        "nombre": p.nombre,
        "foto": p.foto,
        "tiempo_preparacion": float(p.tiempo_preparacion) if p.tiempo_preparacion else None,
        "unidad_tiempo": p.unidad_tiempo,
        "precio_costo": float(p.precio_costo) if p.precio_costo else None,
        "precio_venta": float(p.precio_venta) if p.precio_venta else None,
        "porcentaje_ganancia": float(p.porcentaje_ganancia) if p.porcentaje_ganancia else None,
        "activo": p.activo,
    }
    if incluir_insumos and p.insumos:
        data["insumos"] = [
            {
                "id": pi.id,
                "insumo_id": pi.insumo_id,
                "nombre_insumo": pi.insumo.nombre if pi.insumo else None,
                "unidad_insumo": pi.insumo.unidad if pi.insumo else None,
                "precio_unitario": float(pi.insumo.precio_unitario) if pi.insumo else None,
                "cantidad_necesaria": float(pi.cantidad_necesaria),
            }
            for pi in p.insumos
        ]
    return data


@router.get("")
def listar_productos(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado)
):
    query = db.query(Producto).options(joinedload(Producto.insumos).joinedload(ProductoInsumo.insumo))
    if activo is not None:
        query = query.filter(Producto.activo == activo)
    return [producto_to_dict(p, incluir_insumos=True) for p in query.all()]


@router.get("/{producto_id}")
def obtener_producto(producto_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    p = db.query(Producto).options(
        joinedload(Producto.insumos).joinedload(ProductoInsumo.insumo)
    ).filter(Producto.id == producto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto_to_dict(p, incluir_insumos=True)


class InsumoItem(BaseModel):
    insumo_id: int
    cantidad_necesaria: Decimal


class ProductoCreate(BaseModel):
    nombre: str
    tiempo_preparacion: Optional[Decimal] = None
    unidad_tiempo: Optional[UnidadTiempo] = None
    porcentaje_ganancia: Decimal
    insumos: List[InsumoItem]


class ProductoCostear(BaseModel):
    porcentaje_ganancia: Decimal
    insumos: List[InsumoItem]


@router.post("/costear")
def costear_producto(data: ProductoCostear, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    items = []
    for item in data.insumos:
        insumo = db.query(Insumo).filter(Insumo.id == item.insumo_id).first()
        if not insumo:
            raise HTTPException(status_code=404, detail=f"Insumo {item.insumo_id} no encontrado")
        items.append({
            "precio_unitario": insumo.precio_unitario,
            "cantidad_necesaria": item.cantidad_necesaria,
        })

    costo = calcular_costo_producto(items)
    precio_venta = calcular_precio_venta(costo, data.porcentaje_ganancia)
    return {
        "precio_costo": float(costo),
        "precio_venta": float(precio_venta),
    }


@router.post("")
async def crear_producto(
    nombre: str = Form(...),
    tiempo_preparacion: Optional[float] = Form(None),
    unidad_tiempo: Optional[str] = Form(None),
    porcentaje_ganancia: float = Form(...),
    insumos_json: str = Form(...),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    import json
    insumos_data = json.loads(insumos_json)

    foto_path = None
    if foto and foto.filename:
        ext = foto.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        ruta = os.path.join(UPLOAD_DIR, filename)
        with open(ruta, "wb") as f:
            f.write(await foto.read())
        redimensionar_imagen(ruta)
        foto_path = f"/uploads/{filename}"

    items = []
    for item in insumos_data:
        insumo = db.query(Insumo).filter(Insumo.id == item["insumo_id"]).first()
        if not insumo:
            raise HTTPException(status_code=404, detail=f"Insumo {item['insumo_id']} no encontrado")
        items.append({
            "precio_unitario": insumo.precio_unitario,
            "cantidad_necesaria": item["cantidad_necesaria"],
        })

    costo = calcular_costo_producto(items)
    precio_venta = calcular_precio_venta(costo, Decimal(str(porcentaje_ganancia)))

    producto = Producto(
        nombre=nombre,
        foto=foto_path,
        tiempo_preparacion=tiempo_preparacion,
        unidad_tiempo=unidad_tiempo,
        precio_costo=costo,
        precio_venta=precio_venta,
        porcentaje_ganancia=porcentaje_ganancia,
    )
    db.add(producto)
    db.flush()

    for item in insumos_data:
        pi = ProductoInsumo(
            producto_id=producto.id,
            insumo_id=item["insumo_id"],
            cantidad_necesaria=item["cantidad_necesaria"],
        )
        db.add(pi)

    db.commit()
    db.refresh(producto)
    return {"mensaje": "Producto creado correctamente", "id": producto.id}


@router.put("/{producto_id}")
async def actualizar_producto(
    producto_id: int,
    nombre: Optional[str] = Form(None),
    tiempo_preparacion: Optional[float] = Form(None),
    unidad_tiempo: Optional[str] = Form(None),
    porcentaje_ganancia: Optional[float] = Form(None),
    insumos_json: Optional[str] = Form(None),
    activo: Optional[bool] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    import json
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if foto and foto.filename:
        ext = foto.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        ruta = os.path.join(UPLOAD_DIR, filename)
        with open(ruta, "wb") as f:
            f.write(await foto.read())
        redimensionar_imagen(ruta)
        producto.foto = f"/uploads/{filename}"

    if nombre is not None:
        producto.nombre = nombre
    if tiempo_preparacion is not None:
        producto.tiempo_preparacion = tiempo_preparacion
    if unidad_tiempo is not None:
        producto.unidad_tiempo = unidad_tiempo
    if activo is not None:
        producto.activo = activo

    if insumos_json:
        insumos_data = json.loads(insumos_json)
        db.query(ProductoInsumo).filter(ProductoInsumo.producto_id == producto_id).delete()

        items = []
        for item in insumos_data:
            insumo = db.query(Insumo).filter(Insumo.id == item["insumo_id"]).first()
            if not insumo:
                raise HTTPException(status_code=404, detail=f"Insumo {item['insumo_id']} no encontrado")
            items.append({
                "precio_unitario": insumo.precio_unitario,
                "cantidad_necesaria": item["cantidad_necesaria"],
            })
            pi = ProductoInsumo(
                producto_id=producto_id,
                insumo_id=item["insumo_id"],
                cantidad_necesaria=item["cantidad_necesaria"],
            )
            db.add(pi)

        pg = Decimal(str(porcentaje_ganancia)) if porcentaje_ganancia else producto.porcentaje_ganancia
        costo = calcular_costo_producto(items)
        precio_venta = calcular_precio_venta(costo, pg)
        producto.precio_costo = costo
        producto.precio_venta = precio_venta
        producto.porcentaje_ganancia = pg

    db.commit()
    return {"mensaje": "Producto actualizado correctamente"}


@router.delete("/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    producto.activo = False
    db.commit()
    return {"mensaje": "Producto desactivado correctamente"}
