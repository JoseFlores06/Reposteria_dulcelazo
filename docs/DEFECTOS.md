# Registro de defectos — Dulce Lazo (TC10)

Defectos encontrados al ejecutar los casos del TC9 (pruebas automatizadas en `backend/tests/funcionales`) sobre la **v1.0**, y su corrección en la **v2.0**.
Cada defecto está vinculado en Kiwi TCMS a la ejecución que lo detectó. Los resultados completos están en `backend/tests/resultados/`.

| ID | Defecto | Severidad | Prioridad | Casos | Estado |
|---|---|---|---|---|---|
| [DEF-DL-001](#def-dl-001) | El vendedor puede leer los módulos Insumos y Colaboradores | Alta | Alta | TC-004 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-002](#def-dl-002) | No se puede registrar un insumo con stock inicial 0 | Baja | Media | TC-007 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-003](#def-dl-003) | Alertas y mensajes de stock muestran «UnidadInsumo.mg» en lugar de «mg» | Baja | Media | TC-008, TC-009, TC-011, TC-018, TC-019, TC-020 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-004](#def-dl-004) | Con 0 % de ganancia el precio de venta se redondea por encima del costo | Media | Media | TC-013 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-005](#def-dl-005) | La ganancia estimada del mes incluye ventas pendientes de pago | Alta | Alta | TC-029 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-006](#def-dl-006) | Porcentaje de ganancia de 100 % provoca error 500 | Media | Media | TC-039 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-007](#def-dl-007) | Se puede vender una promoción vencida | Alta | Alta | TC-040 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-008](#def-dl-008) | El registro de usuario no valida nombre, correo ni contraseña | Alta | Alta | TC-049 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-009](#def-dl-009) | GET /api/ventas/verificar-stock responde 422 siempre | Baja | Baja | TC-050 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-010](#def-dl-010) | Se registran ventas con cantidad 0 o negativa (el stock aumenta) | Crítica | Crítica | TC-051 | Corregido en v2.0 (re-test PASSED) |
| [DEF-DL-011](#def-dl-011) | Vender una promoción no descuenta los insumos del producto | Alta | Alta | TC-052 | Corregido en v2.0 (re-test PASSED) |

<a id="def-dl-001"></a>
## DEF-DL-001 · El vendedor puede leer los módulos Insumos y Colaboradores

- **Severidad:** Alta · **Prioridad:** Alta · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-004 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `171272b`

Con un token de rol vendedor, GET /api/insumos y GET /api/colaboradores responden 200 con datos (costos de insumos y datos personales del personal). Finanzas y Usuarios sí responden 403.

**Pasos para reproducir (v1.0)**

1. Iniciar sesión como vendedor@dulcelazo.pe.
2. GET /api/insumos y GET /api/colaboradores con su token.

**Resultado esperado:** HTTP 403 «Se requiere rol de administrador».  
**Resultado obtenido en v1.0:** HTTP 200 con la lista completa.

**Corrección en v2.0:** Las rutas de lectura de insumos, mermas y colaboradores exigen rol admin (requerir_admin). La pantalla Productos ya no pide la lista de insumos cuando el usuario es vendedor.

<a id="def-dl-002"></a>
## DEF-DL-002 · No se puede registrar un insumo con stock inicial 0

- **Severidad:** Baja · **Prioridad:** Media · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-007 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `171272b`

Al registrar un insumo aún no comprado (cantidad 0, precio 0) el sistema responde 400 «La cantidad de compra debe ser mayor a 0».

**Pasos para reproducir (v1.0)**

1. Insumos → Nuevo insumo: Colorante rojo, ml, cantidad 0, precio 0.
2. Guardar.

**Resultado esperado:** El insumo se guarda con stock 0 y estado activo.  
**Resultado obtenido en v1.0:** HTTP 400; el insumo no se crea.

**Corrección en v2.0:** Se acepta cantidad 0 cuando el precio también es 0 (precio unitario 0); cantidades negativas siguen rechazándose.

<a id="def-dl-003"></a>
## DEF-DL-003 · Alertas y mensajes de stock muestran «UnidadInsumo.mg» en lugar de «mg»

- **Severidad:** Baja · **Prioridad:** Media · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-008, TC-009, TC-011, TC-018, TC-019, TC-020 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `cf80b14`

En Python 3.11+ el texto de un Enum dentro de un f-string incluye el nombre de la clase. Afecta la alerta de stock bajo, el error de stock insuficiente, el mensaje de merma y el evento de Google Calendar.

**Pasos para reproducir (v1.0)**

1. Vender 1 «Prueba Huevos x4» con Huevos en 7.
2. Leer alertas_stock.

**Resultado esperado:** «Huevos (3.0 unidad)».  
**Resultado obtenido en v1.0:** «Huevos (3.0 UnidadInsumo.unidad)».

**Corrección en v2.0:** UnidadInsumo y UnidadTiempo definen __str__ para devolver solo el valor («mg», «ml», «unidad»).

<a id="def-dl-004"></a>
## DEF-DL-004 · Con 0 % de ganancia el precio de venta se redondea por encima del costo

- **Severidad:** Media · **Prioridad:** Media · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-013 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `59602a6`

Costear la Torta de Chocolate con 0 % devuelve precio de venta 9.90 sobre un costo de 9.53: se vende con ganancia aunque se pidió 0 %.

**Pasos para reproducir (v1.0)**

POST /api/productos/costear con la receta de la torta y porcentaje_ganancia = 0.

**Resultado esperado:** precio_venta = 9.53.  
**Resultado obtenido en v1.0:** precio_venta = 9.90.

**Corrección en v2.0:** calcular_precio_venta devuelve el costo redondeado a 2 decimales cuando la ganancia es 0 %.

<a id="def-dl-005"></a>
## DEF-DL-005 · La ganancia estimada del mes incluye ventas pendientes de pago

- **Severidad:** Alta · **Prioridad:** Alta · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-029 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `5a04887`

Finanzas → Ventas: con una venta pagada (S/ 23.90) y otra pendiente (S/ 13.50) la ganancia estimada es 21.23 en lugar de 14.37.

**Pasos para reproducir (v1.0)**

1. Registrar Torta de Chocolate (marcar pagada) y Alfajores x6 (pendiente).
2. GET /api/finanzas/ventas-detalle del mes.

**Resultado esperado:** ganancia_total = 14.37 (solo pagadas).  
**Resultado obtenido en v1.0:** ganancia_total = 21.23.

**Corrección en v2.0:** ganancia_total y el margen se calculan solo con ventas pagadas; se agrega ganancia_facturada para lo pendiente. La tarjeta dice «Ganancia estimada (ventas pagadas)».

<a id="def-dl-006"></a>
## DEF-DL-006 · Porcentaje de ganancia de 100 % provoca error 500

- **Severidad:** Media · **Prioridad:** Media · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-039 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `59602a6`

POST /api/productos/costear con porcentaje_ganancia = 100 lanza una excepción no controlada (Internal Server Error).

**Pasos para reproducir (v1.0)**

POST /api/productos/costear con porcentaje_ganancia = 100.

**Resultado esperado:** HTTP 400 «El porcentaje de ganancia no puede ser 100% o más».  
**Resultado obtenido en v1.0:** HTTP 500.

**Corrección en v2.0:** Excepción propia PorcentajeGananciaInvalido convertida en HTTP 400 por un manejador global; también se rechaza un porcentaje negativo.

<a id="def-dl-007"></a>
## DEF-DL-007 · Se puede vender una promoción vencida

- **Severidad:** Alta · **Prioridad:** Alta · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-040 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `44ab844`

Una promoción con fecha_fin pasada y activo = true se vende por API con su precio rebajado. Además la vigencia se evaluaba con hora UTC y no respetaba «activo» cuando la promoción tenía fechas.

**Pasos para reproducir (v1.0)**

1. Crear Promo TC-017 (Pie de Limón, 01/09–30/09/2026).
2. POST /api/ventas con item_tipo = promocion.

**Resultado esperado:** HTTP 4xx «La promoción … no está vigente»; no se crea la venta.  
**Resultado obtenido en v1.0:** HTTP 200; venta registrada.

**Corrección en v2.0:** Nueva regla única esta_vigente() (activo + rango de fechas en hora de Lima), usada por Promociones y Ventas; la venta responde 422 si la promoción no está vigente.

<a id="def-dl-008"></a>
## DEF-DL-008 · El registro de usuario no valida nombre, correo ni contraseña

- **Severidad:** Alta · **Prioridad:** Alta · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-049 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `ec39046`

UsuarioCreate acepta nombres con números o <script>, correos sin @ y contraseñas como «12345678». 30 de 42 pruebas unitarias del TC7 fallaban por esta causa.

**Pasos para reproducir (v1.0)**

POST /api/auth/usuarios con nombres = «Juan3» o correo = «juan.perez.dulcelazo.pe».

**Resultado esperado:** HTTP 422 con el motivo; no se crea el usuario.  
**Resultado obtenido en v1.0:** HTTP 200; usuario creado.

**Corrección en v2.0:** Validadores en UsuarioCreate/UsuarioUpdate: nombres y apellidos 2–100 letras, correo con formato válido (se guarda en minúsculas), contraseña 8–64 con letras y números. El formulario muestra el motivo devuelto por el backend. Resultado: 42/42 pruebas unitarias pasan.

<a id="def-dl-009"></a>
## DEF-DL-009 · GET /api/ventas/verificar-stock responde 422 siempre

- **Severidad:** Baja · **Prioridad:** Baja · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-050 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `44ab844`

La ruta /{venta_id} está declarada antes que /verificar-stock, así que FastAPI intenta convertir «verificar-stock» en un id de venta.

**Pasos para reproducir (v1.0)**

GET /api/ventas/verificar-stock?item_tipo=producto&item_id=1&cantidad=1.

**Resultado esperado:** HTTP 200 con la disponibilidad.  
**Resultado obtenido en v1.0:** HTTP 422 «unable to parse string as an integer».

**Corrección en v2.0:** La ruta /verificar-stock se declara antes que /{venta_id}.

<a id="def-dl-010"></a>
## DEF-DL-010 · Se registran ventas con cantidad 0 o negativa (el stock aumenta)

- **Severidad:** Crítica · **Prioridad:** Crítica · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-051 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `44ab844`

POST /api/ventas acepta cantidad = 0 y cantidad = -2: se crea la venta con total 0 o negativo y, con cantidad negativa, el stock de insumos sube. También acepta una venta sin ítems.

**Pasos para reproducir (v1.0)**

POST /api/ventas con Torta de Chocolate y cantidad = -2.

**Resultado esperado:** HTTP 422; sin venta y sin cambios de stock.  
**Resultado obtenido en v1.0:** HTTP 200; venta con total negativo; Huevos 30 → 38.

**Corrección en v2.0:** cantidad debe ser > 0 y la lista de ítems no puede estar vacía (validación en el esquema VentaCreate).

<a id="def-dl-011"></a>
## DEF-DL-011 · Vender una promoción no descuenta los insumos del producto

- **Severidad:** Alta · **Prioridad:** Alta · **Estado:** Corregido en v2.0 y verificado
- **Casos que lo detectaron:** TC-052 (build v1.0: FAILED → build v2.0: PASSED)
- **Commit de la corrección:** `44ab844`

Al vender una promoción (item_tipo = promocion) el sistema no verifica ni descuenta el stock de la receta del producto o paquete asociado. Además el stock se verificaba ítem por ítem, sin sumar insumos repetidos entre ítems.

**Pasos para reproducir (v1.0)**

1. Crear promoción vigente de Torta de Chocolate.
2. Venderla.
3. Revisar stock de Huevos.

**Resultado esperado:** Huevos 30 → 26.  
**Resultado obtenido en v1.0:** Huevos sigue en 30.

**Corrección en v2.0:** El stock se calcula por pedido completo (requerimientos_pedido) y una promoción se resuelve al producto o paquete al que está ligada.
