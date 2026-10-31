"""
Configuración de las pruebas funcionales (nivel API) de Dulce Lazo.

Las pruebas se ejecutan contra una base de datos MySQL/MariaDB REAL y separada
de la de trabajo. Cada prueba parte de una base limpia:
    reset de tablas  →  SuperUsuario + empresa  →  seed_demo.py  →  usuario vendedor

Configuración (variables de entorno):
    TEST_DATABASE_URL   URL de la BD de pruebas. Su nombre DEBE terminar en "_test"
                        (protección para no borrar la BD de trabajo).
                        Por defecto: mysql+pymysql://root:root@127.0.0.1:3306/dulce_lazo_test

Crear la BD de pruebas una sola vez:
    CREATE DATABASE dulce_lazo_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

Ejecutar (desde la carpeta backend):
    python -m pytest tests/funcionales -v --junitxml=resultados_funcionales.xml
"""
import contextlib
import io
import os
import sys
from pathlib import Path

import pytest

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "mysql+pymysql://root:root@127.0.0.1:3306/dulce_lazo_test",
)
if not TEST_DB_URL.split("?")[0].rstrip("/").endswith("_test"):
    raise RuntimeError(
        "TEST_DATABASE_URL debe apuntar a una base cuyo nombre termine en '_test'. "
        "Las pruebas borran y recrean todas las tablas."
    )

# Debe fijarse ANTES de importar database.py / main.py (el engine se crea al importar).
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas")
os.environ["GROQ_API_KEY"] = ""  # las pruebas nunca llaman a la IA real
# El servidor de Dulce Lazo trabaja en hora de Lima (fechas de entrega, eventos).
os.environ["TZ"] = "America/Lima"
if hasattr(__import__("time"), "tzset"):
    __import__("time").tzset()

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)  # main.py monta la carpeta uploads/ relativa a backend

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from auth import hashear_password  # noqa: E402
from database import SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402
from models.base import Base  # noqa: E402
from models.empresa import Empresa  # noqa: E402
from models.usuario import RolUsuario, Usuario  # noqa: E402
from seed_demo import seed_demo  # noqa: E402

ADMIN = ("admin@dulcelazo.pe", "Admin12345!")
VENDEDOR = ("vendedor@dulcelazo.pe", "Vende1234")


def _reiniciar_bd():
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    db = SessionLocal()
    try:
        db.add(Usuario(nombres="Super", apellidos="Usuario", correo=ADMIN[0],
                       hashed_password=hashear_password(ADMIN[1]),
                       rol=RolUsuario.admin, activo=True))
        db.add(Usuario(nombres="Kevin", apellidos="Puma", correo=VENDEDOR[0],
                       hashed_password=hashear_password(VENDEDOR[1]),
                       rol=RolUsuario.vendedor, activo=True))
        db.add(Empresa(nombre="Dulce Lazo"))
        db.commit()
    finally:
        db.close()

    with contextlib.redirect_stdout(io.StringIO()):
        seed_demo()


@pytest.fixture(autouse=True)
def bd_limpia():
    """Cada caso de prueba empieza con la BD recién sembrada."""
    _reiniciar_bd()
    yield


@pytest.fixture(scope="session")
def client():
    # raise_server_exceptions=False: un error 500 se observa como respuesta 500
    # (igual que lo vería el frontend) en lugar de cortar la prueba.
    return TestClient(app, raise_server_exceptions=False)


def _token(client, correo, password):
    r = client.post("/api/auth/login", data={"username": correo, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return _token(client, *ADMIN)


@pytest.fixture
def vendedor(client):
    return _token(client, *VENDEDOR)


@pytest.fixture
def db():
    sesion = SessionLocal()
    yield sesion
    sesion.close()
