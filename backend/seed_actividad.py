"""
Genera actividad realista (ventas, gastos de marketing, pagos, datos de empresa)
sobre el catalogo ya creado por seed_demo.py, usando la logica real de negocio
(services.stock_service) para que el stock y los totales queden consistentes.
Ejecutar una sola vez, despues de seed_demo.py:
    python seed_actividad.py
"""
import random
from decimal import Decimal
from datetime import timedelta

from database import SessionLocal
from models.insumo import Insumo
from models.producto import Producto
from models.paquete import Paquete
from models.promocion import Promocion
from models.cliente import Cliente
from models.colaborador import Colaborador
from models.usuario import Usuario
from models.empresa import Empresa
from models.venta import Venta, VentaItem, MetodoPago, EstadoPago, EstadoVenta
from models.finanzas import PagoColaborador
from services.stock_service import verificar_stock, descontar_stock
from services.costeo import calcular_costo_producto, calcular_precio_venta
from utils.timezone import now_lima

random.seed(42)


def obtener_precio_item(item_tipo, item_id, db):
    if item_tipo == "producto":
        obj = db.query(Producto).filter(Producto.id == item_id).first()
        return obj.nombre, obj.precio_venta
    if item_tipo == "paquete":
        obj = db.query(Paquete).filter(Paquete.id == item_id).first()
        return obj.nombre, obj.precio_venta
    if item_tipo == "promocion":
        obj = db.query(Promocion).filter(Promocion.id == item_id).first()
        return obj.nombre, obj.precio_promocion


def main():
    db = SessionLocal()
    try:
        if db.query(Venta).count() > 0:
            print("Ya existen ventas. Nada que hacer.")
            return

        # ---- 1. Datos de la empresa (para que la boleta y la pagina se vean completas) ----
        empresa = db.query(Empresa).first()
        if empresa:
            empresa.ruc = "20601234567"
            empresa.direccion = "Av. Los Ceramistas 245, Urb. Las Magnolias"
            empresa.distrito = "Surco, Lima"
            empresa.telefono = "01-273-4589"
            empresa.correo = "contacto@dulcelazo.pe"
            empresa.numero_yape_plin = "987 654 321"
            empresa.nro_cuenta_banco = "191-2345678-0-12"
            empresa.cci = "00219100234567801234"
            db.commit()
            print("Empresa actualizada.")

        # ---- 2. Restock de insumos (simula compras del mes), menos Manjar blanco ----
        # (Manjar blanco se deja con su stock inicial bajo para que la alerta de stock
        #  bajo se dispare de forma organica cuando se vendan varios Alfajores.)
        insumos = db.query(Insumo).all()
        for ins in insumos:
            if ins.nombre == "Manjar blanco":
                continue
            ins.stock_actual = Decimal(str(ins.stock_actual)) * Decimal("9")
        db.commit()
        print("Stock de insumos ampliado (restock simulado).")

        # ---- 3. Ventas de los ultimos 40 dias, usando la logica real de stock ----
        clientes = db.query(Cliente).all()
        productos = db.query(Producto).filter(Producto.activo == True).all()
        paquetes = db.query(Paquete).filter(Paquete.activo == True).all()
        promociones = db.query(Promocion).filter(Promocion.activo == True).all()
        vendedor = db.query(Usuario).order_by(Usuario.id).first()

        metodos = list(MetodoPago)
        fuentes = ["facebook", "instagram", "tiktok", "whatsapp", None]

        catalogo = (
            [("producto", p) for p in productos]
            + [("paquete", p) for p in paquetes]
            + [("promocion", p) for p in promociones]
        )

        creadas = 0
        rechazadas = 0
        hoy = now_lima()

        for dias_atras in range(40, -1, -1):
            fecha_dia = hoy - timedelta(days=dias_atras)
            # mas ventas en dias recientes, fines de semana un poco mas activos
            base = 1 if dias_atras > 30 else 2
            extra = 1 if fecha_dia.weekday() >= 5 else 0
            num_ventas_dia = random.randint(base, base + 2) + extra

            for _ in range(num_ventas_dia):
                cliente = random.choice(clientes)
                n_items = random.choice([1, 1, 2, 2, 3])
                elegidos = random.sample(catalogo, k=min(n_items, len(catalogo)))

                items_ok = []
                for item_tipo, obj in elegidos:
                    cantidad = random.randint(1, 2) if item_tipo != "producto" else random.randint(1, 3)
                    if item_tipo in ("producto", "paquete"):
                        errores = verificar_stock(db, item_tipo, obj.id, cantidad)
                        if errores:
                            continue
                    items_ok.append((item_tipo, obj.id, cantidad))

                if not items_ok:
                    rechazadas += 1
                    continue

                hora = random.randint(9, 20)
                minuto = random.randint(0, 59)
                fecha_venta = fecha_dia.replace(hour=hora, minute=minuto, second=0, microsecond=0)

                pagado = random.random() < 0.82
                venta = Venta(
                    cliente_id=cliente.id,
                    colaborador_id=vendedor.id,
                    metodo_pago=random.choice(metodos),
                    estado_pago=EstadoPago.pagado if pagado else EstadoPago.pendiente,
                    estado_venta=EstadoVenta.completada if pagado else EstadoVenta.en_proceso,
                    notas=None,
                    fecha_hora=fecha_venta,
                    fuente_marketing=random.choice(fuentes),
                    subtotal=Decimal("0"),
                    total=Decimal("0"),
                )
                db.add(venta)
                db.flush()

                total = Decimal("0")
                for item_tipo, item_id, cantidad in items_ok:
                    nombre, precio_unitario = obtener_precio_item(item_tipo, item_id, db)
                    subtotal_item = Decimal(str(precio_unitario)) * cantidad
                    total += subtotal_item
                    db.add(VentaItem(
                        venta_id=venta.id,
                        item_tipo=item_tipo,
                        item_id=item_id,
                        nombre_snapshot=nombre,
                        precio_unitario_snapshot=precio_unitario,
                        cantidad=cantidad,
                        subtotal=subtotal_item,
                    ))
                    if item_tipo in ("producto", "paquete"):
                        descontar_stock(db, item_tipo, item_id, cantidad)

                venta.subtotal = total
                venta.total = total
                creadas += 1

            db.commit()

        print(f"Ventas creadas: {creadas} (items rechazados por falta de stock: {rechazadas})")

        # ---- 4. Pagos a colaboradores (ultimos 2 meses) ----
        colaboradores = db.query(Colaborador).all()
        pagos = []
        for col in colaboradores:
            for mes_atras in [0, 1]:
                pagos.append(PagoColaborador(
                    colaborador_id=col.id,
                    monto=Decimal(str(random.choice([800, 900, 1000, 1100, 1200]))),
                    fecha=hoy - timedelta(days=30 * mes_atras + random.randint(0, 5)),
                    periodo="mensual",
                    notas="Pago de sueldo",
                ))
        for p in pagos:
            db.add(p)
        db.commit()
        print(f"Pagos a colaboradores creados: {len(pagos)}")

        # ---- Resumen de stock final (para verificar que la alerta de stock bajo sea real) ----
        print("\nStock final de insumos:")
        for ins in db.query(Insumo).order_by(Insumo.nombre).all():
            print(f"  {ins.nombre}: {float(ins.stock_actual):.2f} {ins.unidad}")

    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
