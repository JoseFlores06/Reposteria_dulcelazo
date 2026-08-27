from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from database import get_db
from models.marketing import GastoMarketing
from models.venta import Venta
from models.usuario import Usuario
from models.producto import Producto
from models.paquete import Paquete
from models.promocion import Promocion
from auth import requerir_admin
from utils.timezone import now_lima

router = APIRouter()

REDES_SOCIALES = ["facebook", "instagram", "tiktok", "whatsapp", "google_ads", "otro"]


class GastoCreate(BaseModel):
    red_social: str
    monto: Decimal
    descripcion: Optional[str] = None
    num_contactos: int = 0
    num_compradores: int = 0
    periodo: Optional[str] = None


class GastoUpdate(BaseModel):
    red_social: Optional[str] = None
    monto: Optional[Decimal] = None
    descripcion: Optional[str] = None
    num_contactos: Optional[int] = None
    num_compradores: Optional[int] = None
    periodo: Optional[str] = None


def gasto_to_dict(g: GastoMarketing) -> dict:
    total_invertido = float(g.monto)
    costo_por_contacto = round(total_invertido / g.num_contactos, 2) if g.num_contactos else None
    costo_por_comprador = round(total_invertido / g.num_compradores, 2) if g.num_compradores else None
    tasa_conversion = round(g.num_compradores / g.num_contactos * 100, 1) if g.num_contactos else None
    return {
        "id": g.id,
        "red_social": g.red_social,
        "monto": float(g.monto),
        "fecha": g.fecha.isoformat() if g.fecha else None,
        "descripcion": g.descripcion,
        "num_contactos": g.num_contactos,
        "num_compradores": g.num_compradores,
        "periodo": g.periodo,
        "costo_por_contacto": costo_por_contacto,
        "costo_por_comprador": costo_por_comprador,
        "tasa_conversion": tasa_conversion,
    }


# CRUD Gastos

@router.get("/gastos")
def listar_gastos(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    query = db.query(GastoMarketing)
    if anio:
        query = query.filter(extract("year", GastoMarketing.fecha) == anio)
    if mes:
        query = query.filter(extract("month", GastoMarketing.fecha) == mes)
    gastos = query.order_by(GastoMarketing.fecha.desc()).all()

    total_invertido = sum(float(g.monto) for g in gastos)
    total_contactos = sum(g.num_contactos for g in gastos)
    total_compradores = sum(g.num_compradores for g in gastos)

    return {
        "gastos": [gasto_to_dict(g) for g in gastos],
        "resumen": {
            "total_invertido": total_invertido,
            "total_contactos": total_contactos,
            "total_compradores": total_compradores,
            "tasa_conversion_global": round(total_compradores / total_contactos * 100, 1) if total_contactos else None,
            "costo_por_comprador_global": round(total_invertido / total_compradores, 2) if total_compradores else None,
        }
    }


@router.post("/gastos")
def crear_gasto(
    data: GastoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    if data.red_social not in REDES_SOCIALES:
        raise HTTPException(400, detail=f"Red social inválida. Opciones: {REDES_SOCIALES}")
    gasto = GastoMarketing(
        red_social=data.red_social,
        monto=data.monto,
        fecha=now_lima(),
        descripcion=data.descripcion,
        num_contactos=data.num_contactos,
        num_compradores=data.num_compradores,
        periodo=data.periodo,
    )
    db.add(gasto)
    db.commit()
    db.refresh(gasto)
    return gasto_to_dict(gasto)


@router.put("/gastos/{gasto_id}")
def actualizar_gasto(
    gasto_id: int,
    data: GastoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    gasto = db.query(GastoMarketing).filter(GastoMarketing.id == gasto_id).first()
    if not gasto:
        raise HTTPException(404, detail="Gasto no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(gasto, field, value)
    db.commit()
    db.refresh(gasto)
    return gasto_to_dict(gasto)


@router.delete("/gastos/{gasto_id}")
def eliminar_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    gasto = db.query(GastoMarketing).filter(GastoMarketing.id == gasto_id).first()
    if not gasto:
        raise HTTPException(404, detail="Gasto no encontrado")
    db.delete(gasto)
    db.commit()
    return {"mensaje": "Gasto eliminado"}


# Estadísticas de fuentes de marketing en ventas

@router.get("/estadisticas")
def estadisticas_marketing(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Ventas agrupadas por fuente de marketing (de dónde escribió el cliente)."""
    query = db.query(
        Venta.fuente_marketing,
        func.count(Venta.id).label("num_ventas"),
        func.sum(Venta.total).label("total_ingresos"),
    ).filter(Venta.fuente_marketing.isnot(None))

    if anio:
        query = query.filter(extract("year", Venta.fecha_hora) == anio)
    if mes:
        query = query.filter(extract("month", Venta.fecha_hora) == mes)

    resultados = query.group_by(Venta.fuente_marketing).all()

    # Gastos del período por red social
    query_gastos = db.query(
        GastoMarketing.red_social,
        func.sum(GastoMarketing.monto).label("total_gasto"),
    )
    if anio:
        query_gastos = query_gastos.filter(extract("year", GastoMarketing.fecha) == anio)
    if mes:
        query_gastos = query_gastos.filter(extract("month", GastoMarketing.fecha) == mes)
    gastos_por_red = {r.red_social: float(r.total_gasto) for r in query_gastos.group_by(GastoMarketing.red_social).all()}

    data = []
    for r in resultados:
        fuente = r.fuente_marketing or "organico"
        ingresos = float(r.total_ingresos or 0)
        gasto = gastos_por_red.get(fuente, 0)
        roi = round((ingresos - gasto) / gasto * 100, 1) if gasto > 0 else None
        data.append({
            "fuente": fuente,
            "num_ventas": r.num_ventas,
            "total_ingresos": ingresos,
            "total_gasto": gasto,
            "roi": roi,
        })

    return {"por_fuente": data}


# Mensajes WhatsApp con IA

@router.get("/mensajes-whatsapp")
def mensajes_whatsapp(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Genera mensajes de WhatsApp humanizados con Groq basados en productos/promos actuales."""
    from services.groq_service import generar_mensajes_whatsapp

    productos = db.query(Producto).filter(Producto.activo == True).all()
    paquetes = db.query(Paquete).filter(Paquete.activo == True).all()
    promociones = db.query(Promocion).filter(Promocion.activo == True).all()

    prods_data = [{"nombre": p.nombre, "precio": float(p.precio_venta or 0)} for p in productos]
    packs_data = [{"nombre": p.nombre} for p in paquetes]
    promos_data = [{"nombre": p.nombre, "descuento_porcentaje": float(p.descuento_porcentaje or 0)} for p in promociones]

    mensajes = generar_mensajes_whatsapp(prods_data, packs_data, promos_data)
    return {"mensajes": mensajes}


# Prompts para Canva/ChatGPT generados por IA (a medida del negocio)

@router.get("/prompts-canva")
def prompts_canva(
    peticion: Optional[str] = None,
    plataforma: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Prompts publicitarios generados por Groq IA, a medida de los productos y
    promociones activas. `peticion` (texto libre) y `plataforma` son opcionales."""
    from services.groq_service import generar_prompts_canva

    productos = db.query(Producto).filter(Producto.activo == True).all()
    promociones = db.query(Promocion).filter(Promocion.activo == True).all()

    prods_data = [{"nombre": p.nombre} for p in productos]
    promos_data = [{"nombre": p.nombre, "descuento_porcentaje": float(p.descuento_porcentaje or 0)} for p in promociones]

    prompts = generar_prompts_canva(prods_data, promos_data, peticion, plataforma)
    return {"prompts": prompts}
