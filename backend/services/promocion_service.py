"""
Reglas de negocio de las promociones, compartidas por Promociones y Ventas.
"""
from sqlalchemy.orm import Session

from models.producto import Producto
from models.promocion import Promocion, PromocionPaquete
from utils.timezone import now_lima


def esta_vigente(promo: Promocion) -> bool:
    """Una promoción se puede vender solo si está activa y la fecha actual
    (hora de Lima) está dentro de su rango.

    DEF-DL-007: antes, con fechas definidas se ignoraba el campo «activo» y se
    comparaba contra la hora UTC (5 horas adelantada respecto a Lima)."""
    if not promo.activo:
        return False
    ahora = now_lima()
    if promo.fecha_inicio and ahora < promo.fecha_inicio:
        return False
    if promo.fecha_fin and ahora > promo.fecha_fin:
        return False
    return True


def item_de_promocion(db: Session, promo_id: int):
    """Producto o paquete al que está ligada la promoción: ("producto", id),
    ("paquete", id) o (None, None)."""
    prod = db.query(Producto).filter(Producto.promocion_id == promo_id).first()
    if prod:
        return "producto", prod.id
    pp = db.query(PromocionPaquete).filter(PromocionPaquete.promocion_id == promo_id).first()
    if pp:
        return "paquete", pp.paquete_id
    return None, None
