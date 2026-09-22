"""
Datos de prueba para Dulce Lazo.
Ejecutar UNA sola vez despues de correr reset_db.py:
    python seed_demo.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import datetime, timedelta
from database import SessionLocal, engine
from models.base import Base
from models.insumo import Insumo, UnidadInsumo
from models.producto import Producto, ProductoInsumo, UnidadTiempo
from models.paquete import Paquete, PaqueteProducto
from models.promocion import Promocion, PromocionPaquete
from models.cliente import Cliente
from models.colaborador import Colaborador
from services.costeo import calcular_costo_producto, calcular_precio_venta, calcular_costo_paquete


def seed_demo():
    db = SessionLocal()
    try:
        if db.query(Insumo).count() > 0:
            print("AVISO: Ya existen datos. Para regenerar usa: python clear_and_reseed.py")
            return

        print("Creando insumos...")
        # INSUMOS  (cantidad_compra, precio_compra → precio_unitario = precio/cantidad)
        def nuevo_insumo(nombre, unidad, cantidad, precio):
            pu = (Decimal(str(precio)) / Decimal(str(cantidad))).quantize(Decimal("0.000001"))
            return Insumo(nombre=nombre, unidad=unidad, precio_unitario=pu,
                          stock_actual=Decimal(str(cantidad)))

        harina     = nuevo_insumo("Harina de trigo",   UnidadInsumo.mg,    1000, 3.50)
        azucar     = nuevo_insumo("Azucar blanca",     UnidadInsumo.mg,    1000, 3.00)
        mantequilla= nuevo_insumo("Mantequilla",       UnidadInsumo.mg,     500, 8.50)
        huevos     = nuevo_insumo("Huevos",            UnidadInsumo.unidad,  30, 15.00)
        leche      = nuevo_insumo("Leche fresca",      UnidadInsumo.ml,    1000, 4.00)
        esencia    = nuevo_insumo("Esencia de vainilla",UnidadInsumo.ml,    100, 5.00)
        cacao      = nuevo_insumo("Cacao en polvo",    UnidadInsumo.mg,     500, 12.00)
        levadura   = nuevo_insumo("Levadura seca",     UnidadInsumo.mg,     100, 3.00)
        sal        = nuevo_insumo("Sal",               UnidadInsumo.mg,    1000, 1.50)
        aceite     = nuevo_insumo("Aceite vegetal",    UnidadInsumo.ml,    1000, 5.00)
        crema      = nuevo_insumo("Crema de leche",    UnidadInsumo.ml,     500, 10.00)
        manjar     = nuevo_insumo("Manjar blanco",     UnidadInsumo.unidad,  10, 20.00)

        insumos_todos = [harina, azucar, mantequilla, huevos, leche, esencia,
                         cacao, levadura, sal, aceite, crema, manjar]
        for i in insumos_todos:
            db.add(i)
        db.flush()  # obtener IDs

        print("Creando productos...")
        # HELPER: crea Producto + ProductoInsumo y calcula costos
        def crear_producto(nombre, tiempo, unidad_t, ganancia_pct, receta, db):
            """
            receta = [(insumo_obj, cantidad_necesaria), ...]
            """
            items_costeo = [
                {"precio_unitario": ins.precio_unitario, "cantidad_necesaria": cant}
                for ins, cant in receta
            ]
            costo = calcular_costo_producto(items_costeo)
            precio_v = calcular_precio_venta(costo, Decimal(str(ganancia_pct)))

            p = Producto(
                nombre=nombre,
                tiempo_preparacion=tiempo,
                unidad_tiempo=unidad_t,
                precio_costo=costo,
                precio_venta=precio_v,
                porcentaje_ganancia=ganancia_pct,
                activo=True,
            )
            db.add(p)
            db.flush()

            for ins, cant in receta:
                db.add(ProductoInsumo(
                    producto_id=p.id,
                    insumo_id=ins.id,
                    cantidad_necesaria=cant,
                ))
            return p

        # 1. Torta de Chocolate (sirve 8 personas)
        torta_choco = crear_producto(
            "Torta de Chocolate", 4, UnidadTiempo.horas, 60,
            [
                (harina,      250),
                (azucar,      200),
                (mantequilla, 150),
                (huevos,      4),
                (leche,       200),
                (cacao,       100),
                (levadura,    10),
                (sal,         5),
            ], db
        )

        # 2. Cupcakes de Vainilla (pack x6)
        cupcakes = crear_producto(
            "Cupcakes de Vainilla x6", 2, UnidadTiempo.horas, 55,
            [
                (harina,      180),
                (azucar,      150),
                (mantequilla, 100),
                (huevos,      2),
                (leche,       120),
                (esencia,     10),
            ], db
        )

        # 3. Pie de Limon
        pie_limon = crear_producto(
            "Pie de Limon", 3, UnidadTiempo.horas, 60,
            [
                (harina,      200),
                (azucar,      180),
                (mantequilla, 120),
                (huevos,      3),
                (leche,       150),
            ], db
        )

        # 4. Donas Glaseadas (pack x4)
        donas = crear_producto(
            "Donas Glaseadas x4", 2, UnidadTiempo.horas, 55,
            [
                (harina,   300),
                (azucar,   100),
                (levadura, 15),
                (huevos,   2),
                (leche,    150),
                (aceite,   80),
            ], db
        )

        # 5. Cheesecake de Fresa
        cheesecake = crear_producto(
            "Cheesecake de Fresa", 5, UnidadTiempo.horas, 60,
            [
                (harina,      150),
                (azucar,      200),
                (mantequilla, 80),
                (huevos,      3),
                (crema,       300),
            ], db
        )

        # 6. Alfajores (pack x6)
        alfajores = crear_producto(
            "Alfajores x6", 1, UnidadTiempo.horas, 50,
            [
                (harina,      200),
                (azucar,      80),
                (mantequilla, 100),
                (manjar,      2),
            ], db
        )

        # 7. Queque de Platano (sin tiempo para probar advertencia de insumos)
        queque = crear_producto(
            "Queque de Platano", 3, UnidadTiempo.horas, 55,
            [
                (harina,      200),
                (azucar,      160),
                (mantequilla, 80),
                (huevos,      3),
                (leche,       100),
                (esencia,     5),
            ], db
        )

        db.flush()
        print("Creando paquetes...")

        # PAQUETES
        def crear_paquete(nombre, ganancia_pct, items, db):
            """items = [(producto_obj, cantidad), ...]"""
            prods_costeo = [
                {"precio_costo": p.precio_costo, "precio_venta": p.precio_venta, "cantidad": c}
                for p, c in items
            ]
            costo_real, suma_venta = calcular_costo_paquete(prods_costeo)
            precio_v = calcular_precio_venta(costo_real, Decimal(str(ganancia_pct)))

            pak = Paquete(
                nombre=nombre,
                precio_referencia_suma=suma_venta,
                precio_costo_real=costo_real,
                precio_venta=precio_v,
                porcentaje_ganancia=ganancia_pct,
                activo=True,
            )
            db.add(pak)
            db.flush()

            for prod, cant in items:
                db.add(PaqueteProducto(paquete_id=pak.id, producto_id=prod.id, cantidad=cant))
            return pak

        pack_cumple = crear_paquete(
            "Pack Cumpleanos Completo", 55,
            [(torta_choco, 1), (cupcakes, 1)], db
        )

        pack_cafe = crear_paquete(
            "Pack Tarde de Cafe", 50,
            [(pie_limon, 1), (alfajores, 1)], db
        )

        pack_familiar = crear_paquete(
            "Pack Familiar", 55,
            [(torta_choco, 1), (donas, 2), (alfajores, 1)], db
        )

        db.flush()
        print("Creando promociones...")

        # PROMOCIONES
        ahora = datetime.utcnow()

        promo_donas = Promocion(
            nombre="Lunes Feliz - Donas 15% off",
            descripcion="Cada lunes llevate tus donas favoritas con 15% de descuento.",
            precio_original=donas.precio_venta,
            precio_promocion=(donas.precio_venta * Decimal("0.85")).quantize(Decimal("0.01")),
            porcentaje_descuento=Decimal("15"),
            activo=True,
        )
        db.add(promo_donas)
        db.flush()
        donas.promocion_id = promo_donas.id

        promo_pack = Promocion(
            nombre="Fin de Semana - Pack Cumpleanos 10% off",
            descripcion="Celebra este fin de semana con nuestro pack especial a precio reducido.",
            precio_original=pack_cumple.precio_venta,
            precio_promocion=(pack_cumple.precio_venta * Decimal("0.90")).quantize(Decimal("0.01")),
            porcentaje_descuento=Decimal("10"),
            activo=True,
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(days=30),
        )
        db.add(promo_pack)
        db.flush()
        db.add(PromocionPaquete(promocion_id=promo_pack.id, paquete_id=pack_cumple.id, descuento_adicional=0, activo=True))

        promo_cafe = Promocion(
            nombre="Pack Cafe Precio Especial",
            descripcion="Ideal para reuniones. Pie de limon + alfajores a precio de amigo.",
            precio_original=pack_cafe.precio_venta,
            precio_promocion=(pack_cafe.precio_venta * Decimal("0.88")).quantize(Decimal("0.01")),
            porcentaje_descuento=Decimal("12"),
            activo=True,
        )
        db.add(promo_cafe)
        db.flush()
        db.add(PromocionPaquete(promocion_id=promo_cafe.id, paquete_id=pack_cafe.id, descuento_adicional=0, activo=True))

        print("Creando clientes...")
        # CLIENTES
        clientes = [
            Cliente(nombres="Maria", apellidos="Quispe Huanca",
                    telefono="987654321", whatsapp="987654321",
                    correo="maria.quispe@gmail.com", direccion="Jr. Las Flores 123, Miraflores"),
            Cliente(nombres="Carlos", apellidos="Ramos Palomino",
                    telefono="912345678", whatsapp="912345678",
                    correo="carlos.ramos@hotmail.com", direccion="Av. Arequipa 456, San Isidro"),
            Cliente(nombres="Luisa", apellidos="Mendoza Torres",
                    telefono="956789012", whatsapp="956789012",
                    correo="luisa.mendoza@gmail.com", direccion="Calle Los Pinos 789, Surco"),
            Cliente(nombres="Jorge", apellidos="Vargas Condori",
                    telefono="934567890", whatsapp="934567890",
                    correo="jorge.vargas@outlook.com"),
            Cliente(nombres="Ana", apellidos="Ccopa Mamani",
                    telefono="978901234", whatsapp="978901234",
                    correo="ana.ccopa@gmail.com", direccion="Av. La Marina 321, San Miguel"),
            Cliente(nombres="Roberto", apellidos="Flores Suarez",
                    telefono="945678901", whatsapp="945678901"),
        ]
        for c in clientes:
            db.add(c)

        print("Creando colaboradores...")
        # COLABORADORES
        colaboradores = [
            Colaborador(
                nombres="Lucia", apellidos="Apaza Quispe",
                telefono="923456789", whatsapp="923456789",
                correo="lucia.apaza@dulcelazo.pe",
                rol_descripcion="Decoradora de tortas y reposteria fina",
                edad_aproximada=28,
            ),
            Colaborador(
                nombres="Marco", apellidos="Huanca Lima",
                telefono="967890123", whatsapp="967890123",
                correo="marco.huanca@dulcelazo.pe",
                rol_descripcion="Panadero y pastelero principal",
                edad_aproximada=35,
            ),
            Colaborador(
                nombres="Valeria", apellidos="Soto Perez",
                telefono="989012345", whatsapp="989012345",
                correo="valeria.soto@dulcelazo.pe",
                rol_descripcion="Vendedora y atencion al cliente",
                edad_aproximada=24,
            ),
        ]
        for col in colaboradores:
            db.add(col)

        db.commit()

        print("\nDatos de prueba creados correctamente:")
        print(f"  Insumos:       {len(insumos_todos)}")
        print(f"  Productos:     7")
        print(f"  Paquetes:      3")
        print(f"  Promociones:   3")
        print(f"  Clientes:      {len(clientes)}")
        print(f"  Colaboradores: {len(colaboradores)}")
        print("\nPrecios de venta calculados:")
        for prod in [torta_choco, cupcakes, pie_limon, donas, cheesecake, alfajores, queque]:
            db.refresh(prod)
            print(f"  {prod.nombre}: costo S/{float(prod.precio_costo):.2f}  >>  venta S/{float(prod.precio_venta):.2f}")

    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
