"""
IMPORTAR DATOS — corre esto en la laptop NUEVA (la de destino).

Lee 'donitas_backup.json' (generado por exportar_datos.py) y:
  1. Crea la base de datos si no existe.
  2. Crea todas las tablas si no existen.
  3. Inserta los datos (reemplazando lo que hubiera en esas tablas).

Uso en la laptop nueva:
    1) Instala dependencias:   pip install -r requirements.txt
    2) Configura backend\\.env con tu DATABASE_URL local (usuario/clave de tu MySQL).
    3) Copia 'donitas_backup.json' dentro de la carpeta backend.
    4) cd backend
       python importar_datos.py

ADVERTENCIA: vacía las tablas importadas antes de insertar. Todo corre dentro de
una transacción: si algo falla, no se pierde nada (se revierte).
"""
import sys, os, json
from decimal import Decimal
from datetime import datetime, date

from sqlalchemy import create_engine, text, types as satypes, URL
from sqlalchemy.engine import make_url

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, DATABASE_URL
from models.base import Base
import models  # noqa: F401  (registra todas las tablas en Base.metadata)

ENTRADA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donitas_backup.json")


def asegurar_base_existe():
    """Crea la base de datos (schema) si todavía no existe en el servidor MySQL."""
    url = make_url(DATABASE_URL)
    nombre_db = url.database
    # Conexión al servidor SIN seleccionar base (para poder crearla si no existe)
    url_servidor = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=None,
        query=url.query,
    )
    tmp = create_engine(url_servidor)
    with tmp.connect() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS `{nombre_db}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
        conn.commit()
    tmp.dispose()
    print(f"Base de datos '{nombre_db}' lista.")


def convertir(valor, tipo_col):
    """Convierte el valor del JSON al tipo Python correcto según la columna."""
    if valor is None:
        return None
    if isinstance(tipo_col, satypes.Numeric):          # DECIMAL / Numeric
        return Decimal(str(valor))
    if isinstance(tipo_col, satypes.DateTime):
        return datetime.fromisoformat(valor) if isinstance(valor, str) else valor
    if isinstance(tipo_col, satypes.Date):
        return date.fromisoformat(valor) if isinstance(valor, str) else valor
    if isinstance(tipo_col, satypes.Boolean):
        return bool(valor)
    return valor


def main():
    if not os.path.exists(ENTRADA):
        print(f"ERROR: no se encontró el archivo:\n  {ENTRADA}")
        print("Copia 'donitas_backup.json' dentro de la carpeta backend y vuelve a intentar.")
        return

    with open(ENTRADA, encoding="utf-8") as f:
        payload = json.load(f)
    tablas_datos = payload.get("tablas", payload)

    # 1. Base de datos + 2. Esquema
    asegurar_base_existe()
    Base.metadata.create_all(bind=engine)
    print("Tablas verificadas/creadas.")

    orden = Base.metadata.sorted_tables  # respeta dependencias de claves foráneas

    total = 0
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        # Vaciar tablas (en orden inverso por las FKs)
        for tabla in reversed(orden):
            if tabla.name in tablas_datos:
                conn.execute(tabla.delete())

        # Insertar datos (en orden correcto)
        for tabla in orden:
            filas = tablas_datos.get(tabla.name)
            if not filas:
                continue
            convertidas = [
                {col: convertir(fila.get(col), tabla.c[col].type) for col in fila if col in tabla.c}
                for fila in filas
            ]
            conn.execute(tabla.insert(), convertidas)
            total += len(convertidas)
            print(f"  - {tabla.name}: {len(convertidas)} filas")

        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    print(f"\nListo. {total} filas importadas. La base ya tiene tus datos.")


if __name__ == "__main__":
    main()
