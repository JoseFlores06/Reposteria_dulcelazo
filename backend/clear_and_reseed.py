"""
Limpia todos los datos de prueba y regenera nuevos datos frescos.
Ejecutar con:  python clear_and_reseed.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.venta import Venta, VentaItem
from models.paquete import Paquete, PaqueteProducto
from models.producto import Producto, ProductoInsumo
from models.insumo import Insumo
from models.promocion import Promocion
from models.cliente import Cliente
from models.colaborador import Colaborador
from seed_demo import seed_demo


def limpiar_datos():
    db = SessionLocal()
    try:
        db.query(VentaItem).delete(synchronize_session=False)
        db.query(Venta).delete(synchronize_session=False)
        db.query(PaqueteProducto).delete(synchronize_session=False)
        db.query(Paquete).delete(synchronize_session=False)
        db.query(ProductoInsumo).delete(synchronize_session=False)
        db.query(Producto).delete(synchronize_session=False)
        db.query(Insumo).delete(synchronize_session=False)
        db.query(Promocion).delete(synchronize_session=False)
        db.query(Cliente).delete(synchronize_session=False)
        db.query(Colaborador).delete(synchronize_session=False)
        db.commit()
        print("Base de datos limpiada correctamente.")
    except Exception as e:
        db.rollback()
        print(f"Error limpiando: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Limpiando datos antiguos...")
    limpiar_datos()
    print("Generando datos de prueba nuevos...")
    seed_demo()
    print("\nListo.")
