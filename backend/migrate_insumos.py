"""
Migración para la funcionalidad de "comprado" y bajas/mermas de insumos.

- Agrega la columna `comprado` a la tabla `insumos` (si no existe).
- Crea la tabla `mermas_insumos` (si no existe).

No borra datos. Ejecutar con:  python migrate_insumos.py
"""
import sqlalchemy as sa
from database import engine


def columna_existe(conn, tabla: str, columna: str) -> bool:
    res = conn.execute(sa.text(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c
        """
    ), {"t": tabla, "c": columna})
    return res.scalar() > 0


CREATE_MERMAS = """
CREATE TABLE IF NOT EXISTS mermas_insumos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    insumo_id INT NOT NULL,
    cantidad DECIMAL(14,4) NOT NULL,
    motivo VARCHAR(50) NOT NULL DEFAULT 'vencido',
    detalle VARCHAR(200) NULL,
    fecha DATETIME NULL,
    FOREIGN KEY (insumo_id) REFERENCES insumos(id) ON DELETE CASCADE
)
"""

with engine.begin() as conn:
    # 1. Columna comprado en insumos
    if columna_existe(conn, "insumos", "comprado"):
        print("Columna insumos.comprado ya existe.")
    else:
        conn.execute(sa.text(
            "ALTER TABLE insumos ADD COLUMN comprado TINYINT(1) NOT NULL DEFAULT 1"
        ))
        print("Columna insumos.comprado agregada (default 1 = comprado).")

    # 2. Tabla mermas_insumos
    conn.execute(sa.text(CREATE_MERMAS))
    print("Tabla mermas_insumos OK.")

print("\nMigración completada.")
