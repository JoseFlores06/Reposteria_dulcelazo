from database import engine
import sqlalchemy as sa

sql = """
CREATE TABLE IF NOT EXISTS direcciones_clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    etiqueta VARCHAR(50) NOT NULL DEFAULT 'casa',
    direccion VARCHAR(300) NOT NULL,
    distrito VARCHAR(100) NULL,
    referencia VARCHAR(200) NULL,
    principal TINYINT(1) DEFAULT 0,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
)
"""

with engine.connect() as conn:
    try:
        conn.execute(sa.text(sql))
        conn.commit()
        print("direcciones_clientes OK")
    except Exception as e:
        print(f"Error: {e}")
