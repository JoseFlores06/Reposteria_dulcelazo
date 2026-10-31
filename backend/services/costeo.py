import math
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict


class PorcentajeGananciaInvalido(ValueError):
    """El porcentaje de ganancia debe estar entre 0 y 99.99.
    main.py lo convierte en una respuesta HTTP 400 (DEF-DL-006)."""


def redondear_precio_peru(precio: Decimal) -> Decimal:
    """
    Redondea al siguiente precio 'bonito' peruano: .00, .50, .90 o .99
    Ej: 19.65 → 19.90 | 5.12 → 5.50 | 19.91 → 19.99
    """
    precio_float = float(precio)
    entero = math.floor(precio_float)
    decimal_part = round(precio_float - entero, 4)

    for end in [0.00, 0.50, 0.90, 0.99]:
        if decimal_part <= end + 0.0005:
            return Decimal(str(round(entero + end, 2)))
    return Decimal(str(entero + 1))


def calcular_precio_venta(costo_total: Decimal, porcentaje_ganancia: Decimal) -> Decimal:
    """
    Fórmula de margen: precio_venta = costo_total / (1 - porcentaje_ganancia / 100)
    El resultado se redondea al precio peruano más cercano (.00/.50/.90/.99)
    """
    porcentaje_ganancia = Decimal(str(porcentaje_ganancia))
    if porcentaje_ganancia >= 100:
        raise PorcentajeGananciaInvalido("El porcentaje de ganancia no puede ser 100% o más")
    if porcentaje_ganancia < 0:
        raise PorcentajeGananciaInvalido("El porcentaje de ganancia no puede ser negativo")
    if porcentaje_ganancia == 0:
        # DEF-DL-004: sin ganancia el precio de venta es el costo (sin redondeo comercial)
        return Decimal(str(costo_total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    factor = Decimal("1") - (porcentaje_ganancia / Decimal("100"))
    precio_exacto = costo_total / factor
    return redondear_precio_peru(precio_exacto)


def calcular_costo_producto(insumos: List[Dict]) -> Decimal:
    """
    insumos: lista de dicts con keys: precio_unitario, cantidad_necesaria
    """
    total = Decimal("0")
    for item in insumos:
        precio = Decimal(str(item["precio_unitario"]))
        cantidad = Decimal(str(item["cantidad_necesaria"]))
        total += precio * cantidad
    return total.quantize(Decimal("0.0001"))


def calcular_costo_paquete(productos: List[Dict]) -> tuple:
    """
    productos: lista de dicts con keys: precio_costo, precio_venta, cantidad
    Retorna: (costo_real, suma_precios_venta)
    """
    costo_real = Decimal("0")
    suma_venta = Decimal("0")
    for item in productos:
        cantidad = Decimal(str(item["cantidad"]))
        costo_real += Decimal(str(item["precio_costo"])) * cantidad
        suma_venta += Decimal(str(item["precio_venta"])) * cantidad
    return costo_real.quantize(Decimal("0.01")), suma_venta.quantize(Decimal("0.01"))
