import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from decimal import Decimal
import json

from database import get_db
from models.paquete import Paquete, PaqueteProducto
from models.producto import Producto
from models.usuario import Usuario
from auth import requerir_admin, requerir_autenticado
from services.costeo import calcular_costo_paquete, calcular_precio_venta

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


def paquete_to_dict(p: Paquete, incluir_productos: bool = False):
    data = {
        "id": p.id,
        "nombre": p.nombre,
        "foto": p.foto,
        "precio_referencia_suma": float(p.precio_referencia_suma) if p.precio_referencia_suma else None,
        "precio_costo_real": float(p.precio_costo_real) if p.precio_costo_real else None,
        "precio_venta": float(p.precio_venta) if p.precio_venta else None,
        "porcentaje_ganancia": float(p.porcentaje_ganancia) if p.porcentaje_ganancia else None,
        "activo": p.activo,
    }
    if incluir_productos and p.productos:
        data["productos"] = [
            {
                "id": pp.id,
                "producto_id": pp.producto_id,
                "cantidad": pp.cantidad,
                "nombre_producto": pp.producto.nombre if pp.producto else None,
                "foto_producto": pp.producto.foto if pp.producto else None,
                "precio_costo": float(pp.producto.precio_costo) if pp.producto and pp.producto.precio_costo else None,
                "precio_venta": float(pp.producto.precio_venta) if pp.producto and pp.producto.precio_venta else None,
            }
            for pp in p.productos
        ]
    return data


@router.get("")
def listar_paquetes(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado)
):
    query = db.query(Paquete).options(joinedload(Paquete.productos).joinedload(PaqueteProducto.producto))
    if activo is not None:
        query = query.filter(Paquete.activo == activo)
    return [paquete_to_dict(p, incluir_productos=True) for p in query.all()]


@router.get("/{paquete_id}")
def obtener_paquete(paquete_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_autenticado)):
    p = db.query(Paquete).options(
        joinedload(Paquete.productos).joinedload(PaqueteProducto.producto)
    ).filter(Paquete.id == paquete_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return paquete_to_dict(p, incluir_productos=True)


@router.post("/costear")
def costear_paquete(
    productos_data: list,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado)
):
    items = []
    for item in productos_data:
        prod = db.query(Producto).filter(Producto.id == item["producto_id"]).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Producto {item['producto_id']} no encontrado")
        items.append({
            "precio_costo": prod.precio_costo,
            "precio_venta": prod.precio_venta,
            "cantidad": item["cantidad"],
        })
    costo_real, suma_venta = calcular_costo_paquete(items)
    return {"precio_costo_real": float(costo_real), "precio_referencia_suma": float(suma_venta)}


@router.post("")
async def crear_paquete(
    nombre: str = Form(...),
    porcentaje_ganancia: float = Form(...),
    productos_json: str = Form(...),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    productos_data = json.loads(productos_json)

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
    for item in productos_data:
        prod = db.query(Producto).filter(Producto.id == item["producto_id"]).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Producto {item['producto_id']} no encontrado")
        items.append({
            "precio_costo": prod.precio_costo,
            "precio_venta": prod.precio_venta,
            "cantidad": item["cantidad"],
        })

    costo_real, suma_venta = calcular_costo_paquete(items)
    precio_venta = calcular_precio_venta(costo_real, Decimal(str(porcentaje_ganancia)))

    paquete = Paquete(
        nombre=nombre,
        foto=foto_path,
        precio_referencia_suma=suma_venta,
        precio_costo_real=costo_real,
        precio_venta=precio_venta,
        porcentaje_ganancia=porcentaje_ganancia,
    )
    db.add(paquete)
    db.flush()

    for item in productos_data:
        pp = PaqueteProducto(
            paquete_id=paquete.id,
            producto_id=item["producto_id"],
            cantidad=item["cantidad"],
        )
        db.add(pp)

    db.commit()
    db.refresh(paquete)
    return {"mensaje": "Paquete creado correctamente", "id": paquete.id}


@router.put("/{paquete_id}")
async def actualizar_paquete(
    paquete_id: int,
    nombre: Optional[str] = Form(None),
    porcentaje_ganancia: Optional[float] = Form(None),
    productos_json: Optional[str] = Form(None),
    activo: Optional[bool] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin)
):
    paquete = db.query(Paquete).filter(Paquete.id == paquete_id).first()
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")

    if foto and foto.filename:
        ext = foto.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        ruta = os.path.join(UPLOAD_DIR, filename)
        with open(ruta, "wb") as f:
            f.write(await foto.read())
        redimensionar_imagen(ruta)
        paquete.foto = f"/uploads/{filename}"

    if nombre is not None:
        paquete.nombre = nombre
    if activo is not None:
        paquete.activo = activo

    if productos_json:
        productos_data = json.loads(productos_json)
        db.query(PaqueteProducto).filter(PaqueteProducto.paquete_id == paquete_id).delete()

        items = []
        for item in productos_data:
            prod = db.query(Producto).filter(Producto.id == item["producto_id"]).first()
            if not prod:
                raise HTTPException(status_code=404, detail=f"Producto {item['producto_id']} no encontrado")
            items.append({
                "precio_costo": prod.precio_costo,
                "precio_venta": prod.precio_venta,
                "cantidad": item["cantidad"],
            })
            pp = PaqueteProducto(
                paquete_id=paquete_id,
                producto_id=item["producto_id"],
                cantidad=item["cantidad"],
            )
            db.add(pp)

        pg = Decimal(str(porcentaje_ganancia)) if porcentaje_ganancia else paquete.porcentaje_ganancia
        costo_real, suma_venta = calcular_costo_paquete(items)
        precio_venta = calcular_precio_venta(costo_real, pg)
        paquete.precio_costo_real = costo_real
        paquete.precio_referencia_suma = suma_venta
        paquete.precio_venta = precio_venta
        paquete.porcentaje_ganancia = pg

    db.commit()
    return {"mensaje": "Paquete actualizado correctamente"}


@router.delete("/{paquete_id}")
def eliminar_paquete(paquete_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requerir_admin)):
    paquete = db.query(Paquete).filter(Paquete.id == paquete_id).first()
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    paquete.activo = False
    db.commit()
    return {"mensaje": "Paquete desactivado correctamente"}
