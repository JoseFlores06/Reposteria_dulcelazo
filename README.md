# Dulce Lazo

Sistema de gestión para pastelería. Cubre el ciclo completo del negocio: insumos y
stock, costeo de productos, ventas con boleta, clientes, colaboradores, promociones,
finanzas y calendario de pedidos.

## Stack

- **Backend:** FastAPI + SQLAlchemy + MySQL, autenticación con JWT.
- **Frontend:** React + Vite + Tailwind CSS.
- **Integraciones:** Google Calendar (OAuth2) para eventos de pedidos y alertas de
  stock, Groq (IA) para sugerencias de promociones, nombres de producto y análisis
  de ventas.

## Módulos

| Módulo | Qué hace |
|---|---|
| Insumos | Stock de materia prima, mermas, alerta de stock bajo |
| Productos / Paquetes | Costeo automático a partir de la receta de insumos |
| Promociones | Descuentos sobre productos o paquetes, con sugerencias de la IA |
| Ventas | Registro de pedidos, descuento de stock, boleta en PDF, ganancia por venta |
| Clientes | Datos de contacto y direcciones de entrega |
| Colaboradores | Personal y pagos |
| Finanzas | Reportes de insumos, ventas, ganancia y pagos a colaboradores |
| Calendario | Sincronización de pedidos y alertas con Google Calendar |
| Usuarios | Alta de cuentas internas (vendedor / administrador), solo para admins |

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

Crea las tablas y el primer usuario (SuperUsuario) con:

```bash
python reset_db.py
```

El correo y la clave del SuperUsuario se toman de `SUPERUSUARIO_EMAIL` /
`SUPERUSUARIO_PASSWORD` en tu `.env`; si no los defines, se genera una clave
aleatoria y se muestra una sola vez por consola. Con esa cuenta ya puedes entrar
y crear al resto del personal desde el módulo Usuarios ("Nuevo usuario").

Opcionalmente, para tener datos de ejemplo:

```bash
python seed_demo.py        # insumos, productos, paquetes, promociones y clientes
python seed_actividad.py   # ventas y pagos de ejemplo, usando la lógica real de stock
```

Con las tablas ya creadas, levanta el servidor:

```bash
uvicorn main:app --reload --port 8000
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
