from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

from database import get_db
from models.gasto_marketing import GastoMarketing
from models.usuario import Usuario
from auth import requerir_autenticado, requerir_admin

router = APIRouter()

CANALES_VALIDOS = [
    "Redes Sociales", "Facebook Ads", "Instagram Ads", "Google Ads",
    "Flyers / Impresión", "Eventos", "Influencers", "WhatsApp", "Otros",
]


class GastoMarketingCreate(BaseModel):
    fecha: Optional[datetime] = None
    concepto: str = Field(min_length=2, max_length=200)
    canal: Optional[str] = Field(None, max_length=100)
    monto: Decimal = Field(gt=0)
    notas: Optional[str] = None


class GastoMarketingUpdate(BaseModel):
    fecha: Optional[datetime] = None
    concepto: Optional[str] = Field(None, min_length=2, max_length=200)
    canal: Optional[str] = Field(None, max_length=100)
    monto: Optional[Decimal] = Field(None, gt=0)
    notas: Optional[str] = None


def gasto_to_dict(g: GastoMarketing) -> dict:
    return {
        "id": g.id,
        "fecha": g.fecha.isoformat() if g.fecha else None,
        "concepto": g.concepto,
        "canal": g.canal,
        "monto": float(g.monto),
        "notas": g.notas,
    }


@router.get("")
def listar_gastos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado),
):
    gastos = db.query(GastoMarketing).order_by(GastoMarketing.fecha.desc()).all()
    return [gasto_to_dict(g) for g in gastos]


@router.get("/canales")
def listar_canales(_: Usuario = Depends(requerir_autenticado)):
    return CANALES_VALIDOS


@router.get("/{gasto_id}")
def obtener_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_autenticado),
):
    g = db.query(GastoMarketing).filter(GastoMarketing.id == gasto_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Gasto de marketing no encontrado")
    return gasto_to_dict(g)


@router.post("")
def crear_gasto(
    data: GastoMarketingCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    from utils.timezone import now_lima
    g = GastoMarketing(
        fecha=data.fecha or now_lima(),
        concepto=data.concepto,
        canal=data.canal,
        monto=data.monto,
        notas=data.notas,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return gasto_to_dict(g)


@router.patch("/{gasto_id}")
def actualizar_gasto(
    gasto_id: int,
    data: GastoMarketingUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    g = db.query(GastoMarketing).filter(GastoMarketing.id == gasto_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Gasto de marketing no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(g, campo, valor)
    db.commit()
    db.refresh(g)
    return gasto_to_dict(g)


@router.delete("/{gasto_id}")
def eliminar_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requerir_admin),
):
    g = db.query(GastoMarketing).filter(GastoMarketing.id == gasto_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Gasto de marketing no encontrado")
    db.delete(g)
    db.commit()
    return {"mensaje": "Gasto de marketing eliminado"}
