# Cambios

## v2.0 — TC10 (Ejecución de casos, defectos y Software v2.0)

Correcciones de los defectos detectados al ejecutar los casos del TC9 sobre la v1.0
(detalle en `docs/DEFECTOS.md`):

| Defecto | Corrección |
|---|---|
| DEF-DL-001 | Insumos, mermas y colaboradores solo para administradores |
| DEF-DL-002 | Se puede registrar un insumo con stock 0 |
| DEF-DL-003 | Las unidades se muestran como «mg», «ml», «unidad» en alertas y mensajes |
| DEF-DL-004 | Con 0 % de ganancia el precio de venta es el costo |
| DEF-DL-005 | La ganancia estimada del mes solo cuenta ventas pagadas |
| DEF-DL-006 | 100 % de ganancia responde 400 con mensaje (antes 500) |
| DEF-DL-007 | No se vende una promoción vencida o desactivada (vigencia en hora de Lima) |
| DEF-DL-008 | Validación de nombre, correo y contraseña al registrar usuarios |
| DEF-DL-009 | `GET /api/ventas/verificar-stock` vuelve a funcionar |
| DEF-DL-010 | No se aceptan ventas sin ítems ni con cantidad 0 o negativa |
| DEF-DL-011 | Vender una promoción descuenta los insumos del producto o paquete |

Pruebas:

- `backend/tests/funcionales/`: 52 casos automatizados (TC-001 a TC-052) a nivel API sobre MySQL/MariaDB.
- `backend/tests/test_usuarios.py` (TC7): 42/42 pasan (antes 12/42).
- `backend/tests/kiwi/`: carga de casos y resultados en Kiwi TCMS y exportación del reporte.
- Resultados: v1.0 → 34 PASSED, 16 FAILED, 2 BLOCKED · v2.0 → 50 PASSED, 0 FAILED, 2 BLOCKED.
  Los 2 bloqueados son TC-031 y TC-032 (REQ-015 gastos de marketing, fuera del alcance implementado).

## v1.0 — TC6

Caso de uso principal «Registro de Usuario» al 100 %.
