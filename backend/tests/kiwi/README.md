# Kiwi TCMS — cargar casos, resultados y exportar el reporte (TC10)

Requisito: Kiwi TCMS funcionando en Docker (guía de la Semana 5, Parte C1) y un
usuario administrador de Kiwi.

## 1. Generar los resultados reales con pytest

Desde `backend/`, con la BD de pruebas creada una sola vez
(`CREATE DATABASE dulce_lazo_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`):

```bash
pip install -r requirements.txt -r requirements-test.txt
set TEST_DATABASE_URL=mysql+pymysql://root:TU_CLAVE@127.0.0.1:3306/dulce_lazo_test   # PowerShell: $env:TEST_DATABASE_URL="..."
python -m pytest tests/funcionales -v --junitxml=tests/resultados/v2.0_funcionales.xml
python -m pytest tests/test_usuarios.py -v --junitxml=tests/resultados/v2.0_unitarias.xml
```

Los resultados de la v1.0 ya están en `tests/resultados/v1.0_*.xml` (mismas pruebas
ejecutadas sobre el commit `7b977fd`, antes de las correcciones). Para repetirlos:
`git checkout 7b977fd`, correr pytest con `--junitxml=...v1.0_funcionales.xml` y volver con
`git checkout tc10-v2.0`.

## 2. Cargar todo en Kiwi

```bash
cd tests/kiwi
pip install requests reportlab
python cargar_kiwi.py --url https://localhost --usuario TU_USUARIO_KIWI ^
    --v1 ../resultados/v1.0_funcionales.xml --v2 ../resultados/v2.0_funcionales.xml ^
    --unitarias-v2 ../resultados/v2.0_unitarias.xml
```

(Si Kiwi usa el puerto 8443: `--url https://localhost:8443`. En macOS/Linux cambia `^` por `\`.)

Crea en Kiwi: producto **Dulce Lazo**, versión **2026-II**, builds **v1.0** y **v2.0**,
10 categorías, **60 casos CONFIRMED**, el plan **Plan de Pruebas — Dulce Lazo (TC10)** y
3 Test Runs:

| Test Run | Qué contiene |
|---|---|
| Ejecución automatizada (pytest) — Build v1.0 | 34 PASSED · 16 FAILED · 2 BLOCKED · 8 IDLE (UAT) |
| Ejecución automatizada (pytest) — Build v2.0 | 50 PASSED · 2 BLOCKED · 8 IDLE (UAT) |
| Demo en vivo — Build v2.0 | TC-049, TC-044, TC-040, TC-UAT-001 en IDLE, para ejecutarlos en clase |

Cada ejecución fallida tiene su comentario con lo observado y el enlace al defecto
(`docs/DEFECTOS.md`). Se puede ejecutar varias veces: reutiliza lo que ya existe.

## 3. Exportar el reporte (archivo `_Reporte.pdf` del ZIP)

```bash
python exportar_reporte.py --url https://localhost --usuario TU_USUARIO_KIWI ^
    --salida TC10_CalidadyPruebasdeSoftware_Grupo4_Lopez_Fernandez_Flores_Puma_Ordonez_Reporte.pdf
```

Ejecutarlo **después** de la demo para que el run «Demo en vivo» salga con sus resultados.
