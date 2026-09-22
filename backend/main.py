# Punto de entrada de la API. Levanta la app, registra los modelos contra la BD
# y monta cada router bajo /api/<recurso>.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine
from models.base import Base
from models import (
    Usuario, Empresa, Insumo, Producto, ProductoInsumo,
    Paquete, PaqueteProducto, Promocion, PromocionPaquete, Cliente, Colaborador,
    Venta, VentaItem, PagoColaborador, Calendario, DireccionCliente,
    MermaInsumo
)

from routes import (
    auth_router, empresa_router, insumos_router, productos_router,
    paquetes_router, promociones_router, clientes_router,
    colaboradores_router, ventas_router, finanzas_router, calendario_router,
)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Crear carpeta uploads si no existe
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="Dulce Lazo - API",
    description="Sistema de gestión para pastelería Dulce Lazo",
    version="1.0.0",
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos (imágenes)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Rutas
app.include_router(auth_router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(empresa_router, prefix="/api/empresa", tags=["Empresa"])
app.include_router(insumos_router, prefix="/api/insumos", tags=["Insumos"])
app.include_router(productos_router, prefix="/api/productos", tags=["Productos"])
app.include_router(paquetes_router, prefix="/api/paquetes", tags=["Paquetes"])
app.include_router(promociones_router, prefix="/api/promociones", tags=["Promociones"])
app.include_router(clientes_router, prefix="/api/clientes", tags=["Clientes"])
app.include_router(colaboradores_router, prefix="/api/colaboradores", tags=["Colaboradores"])
app.include_router(ventas_router, prefix="/api/ventas", tags=["Ventas"])
app.include_router(finanzas_router, prefix="/api/finanzas", tags=["Finanzas"])
app.include_router(calendario_router, prefix="/api/calendario", tags=["Calendario"])


@app.get("/")
def root():
    return {"mensaje": "API Dulce Lazo funcionando correctamente"}
