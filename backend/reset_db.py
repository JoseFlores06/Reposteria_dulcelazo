"""
Reinicia la base de datos DESDE CERO.

- Elimina TODAS las tablas y todos sus datos.
- Las vuelve a crear vacías.
- Crea los 2 administradores (José y Sandy) y la empresa inicial.

Ejecutar con:  python reset_db.py

⚠️  ADVERTENCIA: esto borra de forma permanente todos los datos actuales
    (ventas, clientes, insumos, productos, usuarios, etc.).
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine, SessionLocal
from models.base import Base

# Importar TODOS los modelos para que Base.metadata conozca cada tabla
from models import (
    Usuario, Empresa, Insumo, Producto, ProductoInsumo,
    Paquete, PaqueteProducto, Promocion, Cliente, Colaborador,
    Venta, VentaItem, PagoColaborador, ConfiguracionGoogle,
    GastoMarketing, DireccionCliente, MermaInsumo,
)
from models.usuario import RolUsuario
from auth import hashear_password


# Administradores a crear (nombre, apellidos, correo de acceso, contraseña)
ADMINS = [
    ("José",  "Flores",   "jose@dulcelazo.pe",  "admin123"),
    ("Sandy", "Gonzalez", "sandy@dulcelazo.pe", "dinosaurio09"),
]


def reset_tablas():
    """Elimina y recrea todas las tablas en una sola conexión, con las
    comprobaciones de claves foráneas desactivadas para evitar errores de orden."""
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    print("Base de datos eliminada y recreada desde cero.")


def crear_admins():
    db = SessionLocal()
    try:
        for nombres, apellidos, correo, password in ADMINS:
            db.add(Usuario(
                nombres=nombres,
                apellidos=apellidos,
                correo=correo,
                hashed_password=hashear_password(password),
                rol=RolUsuario.admin,
                activo=True,
            ))

        # Empresa inicial (necesaria para emitir boletas)
        db.add(Empresa(nombre="Dulce Lazo"))

        db.commit()
        print("Administradores creados:")
        for nombres, _, correo, password in ADMINS:
            print(f"  - {nombres:5s} -> {correo} / {password} (admin)")
    except Exception as e:
        db.rollback()
        print(f"Error creando administradores: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Reiniciando la base de datos (se eliminaran todos los datos)...")
    reset_tablas()
    crear_admins()
    print("\nListo. Base de datos reiniciada con 2 administradores.")
