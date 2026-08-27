"""Script para crear datos iniciales en la base de datos."""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models.base import Base
from models.usuario import Usuario, RolUsuario
from models.empresa import Empresa
from auth import hashear_password


def crear_tablas():
    from models import (
        Usuario, Empresa, Insumo, Producto, ProductoInsumo,
        Paquete, PaqueteProducto, Promocion, Cliente, Colaborador,
        Venta, VentaItem, PagoColaborador, ConfiguracionGoogle
    )
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")


def seed():
    db = SessionLocal()
    try:
        # Verificar si ya existen usuarios
        if db.query(Usuario).count() > 0:
            print("Los seeders ya fueron ejecutados anteriormente.")
            return

        # Crear usuarios admin
        usuarios = [
            Usuario(
                nombres="José",
                apellidos="Flores López",
                correo="jose@dulcelazo.pe",
                hashed_password=hashear_password("abcd1234"),
                rol=RolUsuario.admin,
                activo=True,
            ),
            Usuario(
                nombres="Sandy",
                apellidos="Gonzalez Zuñiga Marcon",
                correo="sandy@dulcelazo.pe",
                hashed_password=hashear_password("sandycita123"),
                rol=RolUsuario.admin,
                activo=True,
            ),
        ]
        db.add_all(usuarios)

        # Crear empresa inicial
        empresa = Empresa(
            nombre="Dulce Lazo",
            ruc=None,
            numero_yape_plin=None,
            nro_cuenta_banco=None,
            cci=None,
        )
        db.add(empresa)

        db.commit()
        print("Seeders ejecutados correctamente.")
        print("  - José Flores López -> jose@dulcelazo.pe / abcd1234 (admin)")
        print("  - Sandy Gonzalez Zuñiga Marcon -> sandy@dulcelazo.pe / sandycita123 (admin)")
    except Exception as e:
        db.rollback()
        print(f"Error en seeders: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    crear_tablas()
    seed()
