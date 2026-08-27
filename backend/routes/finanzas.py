from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from database import get_db
from models.insumo import Insumo
from models.venta import Venta, VentaItem, EstadoPago
from models.colaborador import Colaborador
from models.finanzas import PagoColaborador
from models.marketing import GastoMarketing
from models.usuario import Usuario
from auth import requerir_admin
from utils.timezone import now_lima

router = APIRouter()


class PagoCreate(BaseModel):
    colaborador_id: int
    monto: Decimal
    periodo: Optional[str] = None
    notas: Optional[str] = None


class PagoUpdate(BaseModel):
    monto: Optional[Decimal] = None
    periodo: Optional[str] = None
    notas: Optional[str] = None


def pago_to_dict(p: PagoColaborador) -> dict:
    return {
        "id": p.id,
        "colaborador_id": p.colaborador_id,
        "colaborador_nombre": (
            f"{p.colaborador.nombres} {p.colaborador.apellidos}"
            if p.colaborador else None
        ),
        "monto": float(p.monto),
        "fecha": p.fecha.isoformat() if p.fecha else None,
        "periodo": p.periodo,
        "notas": p.notas,
    }


@router.get("/insumos")
def reporte_insumos(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    # Solo insumos efectivamente comprados cuentan como gasto en Finanzas.
    query = db.query(Insumo).filter(Insumo.comprado == True)
    if anio:
        query = query.filter(extract("year", Insumo.fecha_ingreso) == anio)
    if mes:
        query = query.filter(extract("month", Insumo.fecha_ingreso) == mes)

    insumos = query.order_by(Insumo.nombre).all()
    total = sum(float(i.precio_unitario) * float(i.stock_actual) for i in insumos)

    return {
        "insumos": [
            {
                "id": i.id,
                "nombre": i.nombre,
                "unidad": i.unidad,
                "stock_actual": float(i.stock_actual),
                "precio_unitario": float(i.precio_unitario),
                "total_valor": float(i.precio_unitario) * float(i.stock_actual),
                "fecha_ingreso": i.fecha_ingreso.isoformat() if i.fecha_ingreso else None,
            }
            for i in insumos
        ],
        "total_gasto": total,
    }


@router.get("/ventas")
def reporte_ventas(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    query = db.query(Venta).options(joinedload(Venta.cliente))
    if anio:
        query = query.filter(extract("year", Venta.fecha_hora) == anio)
    if mes:
        query = query.filter(extract("month", Venta.fecha_hora) == mes)

    ventas = query.order_by(Venta.fecha_hora.desc()).all()
    total_ingresos = sum(float(v.total) for v in ventas if v.estado_pago == EstadoPago.pagado)

    return {
        "ventas": [
            {
                "id": v.id,
                "fecha_hora": v.fecha_hora.isoformat() if v.fecha_hora else None,
                "cliente": f"{v.cliente.nombres} {v.cliente.apellidos}" if v.cliente else "Sin cliente",
                "total": float(v.total),
                "estado_pago": v.estado_pago,
                "estado_venta": v.estado_venta,
            }
            for v in ventas
        ],
        "total_ingresos": total_ingresos,
        "num_ventas": len(ventas),
    }


@router.get("/ganancia")
def reporte_ganancia(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    query_ventas = db.query(Venta).filter(Venta.estado_pago == EstadoPago.pagado)
    query_insumos = db.query(Insumo).filter(Insumo.comprado == True)

    if anio:
        query_ventas = query_ventas.filter(extract("year", Venta.fecha_hora) == anio)
        query_insumos = query_insumos.filter(extract("year", Insumo.fecha_ingreso) == anio)
    if mes:
        query_ventas = query_ventas.filter(extract("month", Venta.fecha_hora) == mes)
        query_insumos = query_insumos.filter(extract("month", Insumo.fecha_ingreso) == mes)

    ingresos = sum(float(v.total) for v in query_ventas.all())
    gasto_insumos = sum(
        float(i.precio_unitario) * float(i.stock_actual) for i in query_insumos.all()
    )

    return {
        "ingresos_totales": ingresos,
        "gasto_insumos": gasto_insumos,
        "ganancia_estimada": ingresos - gasto_insumos,
    }


@router.get("/pagos-colaboradores")
def listar_pagos(
    colaborador_id: Optional[int] = None,
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    query = db.query(PagoColaborador).options(joinedload(PagoColaborador.colaborador))
    if colaborador_id:
        query = query.filter(PagoColaborador.colaborador_id == colaborador_id)
    if anio:
        query = query.filter(extract("year", PagoColaborador.fecha) == anio)
    if mes:
        query = query.filter(extract("month", PagoColaborador.fecha) == mes)

    pagos = query.order_by(PagoColaborador.fecha.desc()).all()
    return [pago_to_dict(p) for p in pagos]


@router.post("/pagos-colaboradores")
def registrar_pago(
    data: PagoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    colaborador = db.query(Colaborador).filter(Colaborador.id == data.colaborador_id).first()
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    pago = PagoColaborador(
        colaborador_id=data.colaborador_id,
        monto=data.monto,
        periodo=data.periodo,
        notas=data.notas,
        fecha=now_lima(),
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    db.refresh(pago, ["colaborador"])
    return {"mensaje": "Pago registrado correctamente", "pago": pago_to_dict(pago)}


@router.put("/pagos-colaboradores/{pago_id}")
def actualizar_pago(
    pago_id: int,
    data: PagoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    pago = db.query(PagoColaborador).options(
        joinedload(PagoColaborador.colaborador)
    ).filter(PagoColaborador.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if data.monto is not None:
        pago.monto = data.monto
    if data.periodo is not None:
        pago.periodo = data.periodo
    if data.notas is not None:
        pago.notas = data.notas

    db.commit()
    return {"mensaje": "Pago actualizado", "pago": pago_to_dict(pago)}


@router.delete("/pagos-colaboradores/{pago_id}")
def eliminar_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    pago = db.query(PagoColaborador).filter(PagoColaborador.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    db.delete(pago)
    db.commit()
    return {"mensaje": "Pago eliminado correctamente"}


@router.get("/resumen-groq")
def resumen_con_groq(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Genera un análisis de ventas con recomendaciones usando Groq IA."""
    from services.groq_service import analizar_ventas
    from models.venta import VentaItem
    from sqlalchemy import func

    query = db.query(Venta).options(joinedload(Venta.items)).filter(Venta.estado_pago == EstadoPago.pagado)
    if anio:
        query = query.filter(extract("year", Venta.fecha_hora) == anio)
    if mes:
        query = query.filter(extract("month", Venta.fecha_hora) == mes)

    ventas = query.all()
    ingresos = sum(float(v.total) for v in ventas)
    total_ventas = len(ventas)
    promedio = ingresos / total_ventas if total_ventas > 0 else 0

    # Producto más vendido
    producto_top = "N/A"
    conteo: dict[str, int] = {}
    for v in ventas:
        for item in v.items:
            conteo[item.nombre_snapshot] = conteo.get(item.nombre_snapshot, 0) + item.cantidad
    if conteo:
        producto_top = max(conteo, key=conteo.get)

    from calendar import month_name
    MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    mes_str = MESES[mes - 1] if mes else "todo el período"
    if anio:
        mes_str = f"{mes_str} {anio}"

    resumen = {
        "mes": mes_str,
        "total_ventas": total_ventas,
        "ingresos": ingresos,
        "promedio": promedio,
        "producto_top": producto_top,
    }

    analisis = analizar_ventas(resumen)
    return {**resumen, "analisis_ia": analisis}


@router.get("/ventas-detalle")
def ventas_con_ganancia(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Lista ventas con desglose de ganancia por venta y por item."""
    query = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.items),
    )
    if anio:
        query = query.filter(extract("year", Venta.fecha_hora) == anio)
    if mes:
        query = query.filter(extract("month", Venta.fecha_hora) == mes)

    ventas = query.order_by(Venta.fecha_hora.desc()).all()

    resultado = []
    total_ingresos = 0
    total_costo = 0

    for v in ventas:
        items_detalle = []
        costo_venta = 0.0
        for item in v.items:
            precio_venta_u = float(item.precio_unitario_snapshot)
            cantidad = item.cantidad
            subtotal_venta = precio_venta_u * cantidad

            # Costo aproximado: buscamos en el producto si existe
            from models.producto import Producto
            costo_u = 0.0
            if item.item_tipo == "producto":
                prod = db.query(Producto).filter(Producto.id == item.item_id).first()
                if prod and prod.precio_costo:
                    costo_u = float(prod.precio_costo)

            costo_item = costo_u * cantidad
            costo_venta += costo_item
            ganancia_item = subtotal_venta - costo_item
            margen_item = round(ganancia_item / subtotal_venta * 100, 1) if subtotal_venta > 0 else 0

            items_detalle.append({
                "nombre": item.nombre_snapshot,
                "tipo": item.item_tipo,
                "cantidad": cantidad,
                "precio_venta_unit": precio_venta_u,
                "costo_unit": costo_u,
                "subtotal_venta": round(subtotal_venta, 2),
                "costo_total": round(costo_item, 2),
                "ganancia": round(ganancia_item, 2),
                "margen_pct": margen_item,
            })

        total_venta = float(v.total)
        ganancia_venta = total_venta - costo_venta
        margen_venta = round(ganancia_venta / total_venta * 100, 1) if total_venta > 0 else 0

        total_ingresos += total_venta
        total_costo += costo_venta

        resultado.append({
            "id": v.id,
            "fecha_hora": v.fecha_hora.isoformat() if v.fecha_hora else None,
            "cliente": f"{v.cliente.nombres} {v.cliente.apellidos}" if v.cliente else "Sin cliente",
            "fuente_marketing": v.fuente_marketing,
            "metodo_pago": v.metodo_pago,
            "estado_pago": v.estado_pago,
            "estado_venta": v.estado_venta,
            "total_venta": total_venta,
            "costo_estimado": round(costo_venta, 2),
            "ganancia_estimada": round(ganancia_venta, 2),
            "margen_pct": margen_venta,
            "items": items_detalle,
        })

    ganancia_total = total_ingresos - total_costo
    margen_total = round(ganancia_total / total_ingresos * 100, 1) if total_ingresos > 0 else 0

    return {
        "ventas": resultado,
        "resumen": {
            "num_ventas": len(resultado),
            "total_ingresos": round(total_ingresos, 2),
            "total_costo": round(total_costo, 2),
            "ganancia_total": round(ganancia_total, 2),
            "margen_promedio": margen_total,
        }
    }


@router.get("/dashboard")
def dashboard(
    periodo: Optional[str] = "mes",
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Datos para el dashboard de explotación: ventas por día, método de pago, producto top, etc."""
    from sqlalchemy import case
    from models.venta import VentaItem

    query = db.query(Venta)
    if anio:
        query = query.filter(extract("year", Venta.fecha_hora) == anio)
    if mes:
        query = query.filter(extract("month", Venta.fecha_hora) == mes)

    ventas = query.options(joinedload(Venta.items)).all()

    # Por día de la semana
    dias_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    por_dia = {d: 0 for d in dias_nombres}
    por_dia_ingresos = {d: 0.0 for d in dias_nombres}

    # Por mes
    meses_nombres = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    por_mes = {m: 0 for m in meses_nombres}
    por_mes_ingresos = {m: 0.0 for m in meses_nombres}

    # Por método de pago
    metodos: dict[str, int] = {}

    # Por fuente marketing
    fuentes: dict[str, int] = {}

    # Productos más vendidos
    productos_conteo: dict[str, int] = {}

    # Ventas por hora
    por_hora = {str(h): 0 for h in range(24)}

    for v in ventas:
        if v.fecha_hora:
            dia_idx = v.fecha_hora.weekday()  # 0=Lun
            dia_str = dias_nombres[dia_idx]
            mes_idx = v.fecha_hora.month - 1
            mes_str = meses_nombres[mes_idx]
            hora_str = str(v.fecha_hora.hour)

            por_dia[dia_str] += 1
            por_dia_ingresos[dia_str] += float(v.total)
            por_mes[mes_str] += 1
            por_mes_ingresos[mes_str] += float(v.total)
            por_hora[hora_str] += 1

        metodo = v.metodo_pago or "otro"
        metodos[metodo] = metodos.get(metodo, 0) + 1

        fuente = v.fuente_marketing or "organico"
        fuentes[fuente] = fuentes.get(fuente, 0) + 1

        for item in v.items:
            productos_conteo[item.nombre_snapshot] = productos_conteo.get(item.nombre_snapshot, 0) + item.cantidad

    top_productos = sorted(productos_conteo.items(), key=lambda x: x[1], reverse=True)[:8]

    return {
        "por_dia_semana": [{"dia": d, "ventas": por_dia[d], "ingresos": round(por_dia_ingresos[d], 2)} for d in dias_nombres],
        "por_mes": [{"mes": m, "ventas": por_mes[m], "ingresos": round(por_mes_ingresos[m], 2)} for m in meses_nombres],
        "por_hora": [{"hora": f"{h}:00", "ventas": por_hora[str(h)]} for h in range(7, 22)],
        "por_metodo_pago": [{"metodo": k, "cantidad": v} for k, v in metodos.items()],
        "por_fuente_marketing": [{"fuente": k, "cantidad": v} for k, v in fuentes.items()],
        "top_productos": [{"nombre": n, "cantidad": c} for n, c in top_productos],
        "totales": {
            "num_ventas": len(ventas),
            "ingresos": round(sum(float(v.total) for v in ventas), 2),
            "ticket_promedio": round(sum(float(v.total) for v in ventas) / len(ventas), 2) if ventas else 0,
        }
    }


@router.get("/marketing")
def resumen_marketing(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    """Gastos de marketing para la sub-pestaña en Finanzas."""
    query = db.query(GastoMarketing)
    if anio:
        query = query.filter(extract("year", GastoMarketing.fecha) == anio)
    if mes:
        query = query.filter(extract("month", GastoMarketing.fecha) == mes)

    gastos = query.order_by(GastoMarketing.fecha.desc()).all()
    total = sum(float(g.monto) for g in gastos)

    return {
        "gastos": [
            {
                "id": g.id,
                "red_social": g.red_social,
                "monto": float(g.monto),
                "fecha": g.fecha.isoformat() if g.fecha else None,
                "descripcion": g.descripcion,
                "num_contactos": g.num_contactos,
                "num_compradores": g.num_compradores,
                "periodo": g.periodo,
            }
            for g in gastos
        ],
        "total_invertido": total,
        "num_gastos": len(gastos),
    }
