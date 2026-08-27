"""
EXPORTAR DATOS — corre esto en la laptop que YA tiene los datos.

Vuelca TODO el contenido de la base de datos a un único archivo portable:
    donitas_backup.json

Uso:
    cd backend
    python exportar_datos.py

Luego copia el archivo 'donitas_backup.json' (junto con el proyecto) a la otra
laptop y ahí ejecuta 'python importar_datos.py'.

No modifica nada: solo lee. No necesita mysqldump.
"""
import sys, os, json, base64
from decimal import Decimal
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from models.base import Base
import models  # noqa: F401  (registra todas las tablas en Base.metadata)

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donitas_backup.json")


def jsonificar(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return base64.b64encode(v).decode("ascii")
    return v


def main():
    datos = {}
    total = 0
    print("Exportando tablas...")
    with engine.connect() as conn:
        for tabla in Base.metadata.sorted_tables:
            filas = conn.execute(tabla.select()).mappings().all()
            datos[tabla.name] = [{k: jsonificar(v) for k, v in fila.items()} for fila in filas]
            total += len(filas)
            print(f"  - {tabla.name}: {len(filas)} filas")

    payload = {
        "_meta": {"exportado_en": datetime.now().isoformat(), "total_filas": total},
        "tablas": datos,
    }
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, default=str)

    print(f"\nListo. {total} filas exportadas a:\n  {SALIDA}")
    print("Copia ese archivo a la otra laptop y corre:  python importar_datos.py")


if __name__ == "__main__":
    main()
