# Dulce Lazo

Sistema de gestión para pastelería. Cubre el ciclo completo del negocio: insumos y
stock, costeo de productos, ventas con boleta, clientes, colaboradores, finanzas,
marketing y calendario de pedidos.

## Stack

- **Backend:** FastAPI + SQLAlchemy + MySQL, autenticación con JWT.
- **Frontend:** React + Vite + Tailwind CSS.
- **Integraciones:** Google Calendar (OAuth2) para eventos de pedidos y alertas de
  stock, Groq (IA) para sugerencias de marketing y análisis de ventas.

## Módulos

| Módulo | Qué hace |
|---|---|
| Insumos | Stock de materia prima, mermas, alerta de stock bajo |
| Productos / Paquetes | Costeo automático a partir de la receta de insumos |
| Ventas | Registro de pedidos, descuento de stock, boleta en PDF |
| Clientes | Datos de contacto y direcciones de entrega |
| Colaboradores | Personal y pagos |
| Finanzas | Reportes de ingresos, costos y ganancia |
| Marketing | Gastos por red social, ROI, mensajes y prompts publicitarios con IA |
| Calendario | Sincronización de pedidos y alertas con Google Calendar |

## Requisitos

- Python 3.11+
- Node.js 18+
- MySQL 8+

## Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

Copia `.env.example` a `.env` y completa tus credenciales (usuario/clave de MySQL,
`SECRET_KEY` propia, y opcionalmente `GROQ_API_KEY` / credenciales de Google si vas
a usar esas integraciones):

```bash
cp .env.example .env
```

Crea la base de datos (el nombre debe coincidir con el de tu `DATABASE_URL`):

```sql
CREATE DATABASE dulce_lazo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Levanta el servidor (crea las tablas automáticamente al iniciar):

```bash
uvicorn main:app --reload --port 8000
```

Para tener datos iniciales, corre uno de estos scripts una sola vez:

```bash
python seed.py         # solo los 2 usuarios administradores + empresa
python seed_demo.py    # además, insumos/productos/paquetes de ejemplo
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

La app queda disponible en `http://localhost:5173`. El proxy de Vite ya está
configurado para redirigir `/api` y `/uploads` a `http://127.0.0.1:8000`.

## Estructura

```
backend/
  models/        # Tablas SQLAlchemy
  routes/        # Endpoints de la API, uno por recurso
  services/      # Lógica de negocio (costeo, stock, PDF, Google Calendar, IA)
  auth.py        # JWT y dependencias de autenticación/autorización
  main.py        # Registro de routers y configuración de la app

frontend/
  src/pages/         # Una página por módulo
  src/components/    # Layout y componentes compartidos
  src/context/       # Contexto de autenticación
  src/api/           # Llamadas a la API (axios)
```
