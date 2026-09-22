"""
Reinicia la base de datos DESDE CERO.

- Elimina TODAS las tablas y todos sus datos.
- Las vuelve a crear vacías.
- Crea un SuperUsuario inicial y la empresa vacía.

Ejecutar con:  python reset_db.py

⚠️  ADVERTENCIA: esto borra de forma permanente todos los datos actuales
    (ventas, clientes, insumos, productos, usuarios, etc.).
"""
import sys, os, secrets
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine, SessionLocal
from models.base import Base

# Importar TODOS los modelos para que Base.metadata conozca cada tabla
from models import (
    Usuario, Empresa, Insumo, Producto, ProductoInsumo,
    Paquete, PaqueteProducto, Promocion, PromocionPaquete, Cliente, Colaborador,
    Venta, VentaItem, PagoColaborador, Calendario,
    DireccionCliente, MermaInsumo,
)
from models.usuario import RolUsuario
from auth import hashear_password


# Cuenta inicial para poder entrar por primera vez y crear al resto del
# personal desde Usuarios -> Nuevo usuario. La contraseña se toma de una
# variable de entorno; si no se define, se genera una aleatoria y se
# muestra una sola vez por consola (nunca queda escrita en el repositorio).
SUPERUSUARIO_CORREO = os.getenv("SUPERUSUARIO_EMAIL", "admin@dulcelazo.pe")
SUPERUSUARIO_PASSWORD = os.getenv("SUPERUSUARIO_PASSWORD") or secrets.token_urlsafe(12)
SUPERUSUARIO = ("Super", "Usuario", SUPERUSUARIO_CORREO, SUPERUSUARIO_PASSWORD)


def reset_tablas():
    """Elimina y recrea todas las tablas en una sola conexión, con las
    comprobaciones de claves foráneas desactivadas para evitar errores de orden."""
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    print("Base de datos eliminada y recreada desde cero.")


def crear_superusuario():
    db = SessionLocal()
    try:
        nombres, apellidos, correo, password = SUPERUSUARIO
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
        print(f"SuperUsuario creado: {correo} / {password}")
        print("Cambia esta contraseña o crea tu propio admin desde Usuarios y desactiva este.")
    except Exception as e:
        db.rollback()
        print(f"Error creando el superusuario: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Reiniciando la base de datos (se eliminaran todos los datos)...")
    reset_tablas()
    crear_superusuario()
    print("\nListo. Base de datos reiniciada con un SuperUsuario.")
