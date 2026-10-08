# Bitácora de refactorización

**Nombre:**
**Matrícula:**
**Fecha:** 8 de octubre de 2026

Registra aquí **cada refactorización** que realices con Claude Code. Copia el
prompt tal cual lo escribiste (o un resumen fiel si fue una conversación larga),
describe el cambio que se aplicó al código y justifica por qué mejora la calidad.
Después de cada cambio ejecuta `pytest` y anota el resultado.

## Línea base (antes de refactorizar)

| Métrica | Valor inicial |
|---------|---------------|
| `pytest` | 20 pruebas, 20 pasan |
| `ruff check src` | 20 errores |
| Complejidad de `registrar_venta` | 12 (límite: 10) |
| Complejidad de `menu` | 17 (límite: 10) |

## Refactorizaciones

| #  | Prompt usado | Cambio realizado | Justificación | Tests OK |
|----|--------------|------------------|---------------|----------|
| 0  | «Crea un `CLAUDE.md` con el contexto del proyecto (qué hace, cómo correr las pruebas, reglas que la IA debe respetar — por ejemplo, *no modificar los tests*) y un `.claudeignore` con lo que no debe leer (entornos virtuales, cachés, datos generados).» | Se crearon `CLAUDE.md` (contexto, comandos, reglas, API pública que consumen los tests, reglas de negocio fijadas por la suite y catálogo de code smells) y `.claudeignore` (entornos virtuales, cachés, artefactos de pytest/ruff, datos generados, basura de macOS). | No es refactorización de código, sino la configuración que pide el punto 1 del reto. Documentar la API intocable evita el error más caro del ejercicio: renombrar algo que los tests invocan. Se decidió **no** ignorar `tests/` ni `pyproject.toml` porque Claude necesita leerlos para saber qué comportamiento está fijado; la prohibición de *modificarlos* vive en `CLAUDE.md`. | 20/20 ✔ (sin cambios en `src/`) |
| 1  | «Dame un diagnóstico: qué *code smells* detectas y recomiéndame 10 refactorizaciones. Prioriza.» | Diagnóstico sin cambios en el código: mapeo de los 20 errores de ruff a los módulos, identificación de 10 smells estructurales que ruff no detecta y plan priorizado de 10 refactorizaciones por impacto/riesgo. | Refactorizar sin diagnóstico previo lleva a tocar lo cosmético y dejar lo estructural. El orden importa: eliminar código muerto antes de refactorizar evita trabajar sobre funciones que nadie llama, y extraer el cálculo duplicado antes de partir `registrar_venta` hace que los pasos siguientes sean más pequeños. | 20/20 ✔ (sin cambios en `src/`) |
| 2  | «Empecemos aplicando la primera refactorización: extraer el motor de cálculo a una sola función.» | Se extrajo todo el cálculo económico de `registrar_venta` y `cotizar` a una sola función `calcular_importes(precio, cantidad, cliente="")` en `src/gestor.py`, apoyada en dos auxiliares (`_descuento_por_volumen` y `_descuento_extra_vip`) y en un `NamedTuple` `ImportesVenta` que transporta el desglose. `registrar_venta` pasó de 21 líneas de cálculo a 1; `cotizar` pasó de 10 líneas a 1. | **Elimina la duplicación más grave del proyecto.** La regla de descuentos e IVA estaba escrita dos veces, con dos redacciones distintas del mismo `if/else`: cambiar la tasa de IVA obligaba a editar dos lugares y olvidar uno producía cotizaciones que no coincidían con el cobro (precisamente lo que vigila `test_cotizar_coincide_con_el_total_de_la_venta`). Ahora hay una sola fuente de verdad. Además aplana la pirámide de 4 `if` anidados del bloque VIP convirtiéndola en guard clauses, lo que baja la complejidad de `registrar_venta` de 12 a por debajo del límite. | 20/20 ✔ |

| 3  | «Haz la siguiente refactorización.» (eliminar código muerto, según la prioridad acordada en el diagnóstico) | Se eliminaron cuatro piezas de código que nadie invoca: la función `calcular_descuento_viejo` (fórmula de descuentos vigente hasta 2023), la función `reporteViejoCSV`, la bandera global `MODO_DEBUG` y el bloque comentado `exportar_txt`. De paso se quitó el `import os` de `reportes.py`, que quedaba sin uso. En total, ~25 líneas menos. | El código muerto miente sobre el sistema: `calcular_descuento_viejo` sugiere que existe una segunda regla de descuentos vigente, y `MODO_DEBUG` insinúa un modo de depuración que nunca se lee. Ambos obligan a quien lee el módulo a razonar sobre rutas que no existen, y a quien refactoriza, a mantenerlas. El historial de git ya conserva el código si alguna vez hiciera falta, así que «dejarlo por si acaso» no aporta nada. Se verificó con una búsqueda en todo el proyecto que ninguno tuviera una sola llamada. | 20/20 ✔ |

| 4  | «Continúa con la #4.» (constantes con nombre para los números mágicos) | Se declararon 11 constantes al inicio de `src/gestor.py`, agrupadas bajo el encabezado «Reglas de negocio de la tienda»: `MONTO_DESCUENTO_ALTO`, `TASA_DESCUENTO_ALTO`, `MONTO_DESCUENTO_MEDIO`, `TASA_DESCUENTO_MEDIO`, `PREFIJO_CLIENTE_VIP`, `MONTO_MINIMO_VIP`, `TASA_DESCUENTO_VIP`, `TASA_IVA`, `STOCK_MINIMO`, `DECIMALES_MONEDA` y `FORMATO_FECHA`. Se sustituyeron todas sus apariciones en `gestor.py` y `reportes.py`. | Los literales no decían qué significaban: `0.16` podía ser el IVA o cualquier otra tasa, y `500` convivía con `200` sin que el lector supiera cuál era un umbral de volumen y cuál un mínimo VIP. Más grave aún, **el `5` del stock mínimo estaba escrito dos veces** en `reportes.py` (en `productos_stock_bajo` y en `reporte_inventario`): cambiar el umbral en un solo sitio habría hecho que la alerta del reporte dejara de coincidir con la lista de productos en riesgo. Ahora cada regla vive en un solo lugar y su nombre explica la intención. | 20/20 ✔ |

> Agrega más filas si realizas más de 5 refactorizaciones.

### Detalle de la refactorización #2

**Efecto medible**

| Métrica | Antes | Después |
|---------|-------|---------|
| `pytest` | 20/20 | 20/20 |
| `ruff check src` | 20 errores | 15 errores |
| Complejidad de `registrar_venta` | 12 (C901) | bajo el límite |
| Lugares donde vive la regla de descuento+IVA | 2 | 1 |

Errores de ruff cerrados por este cambio: `C901` en `registrar_venta`, `SIM108`
(ternario) y los tres `SIM102` (ifs colapsables).

### Detalle de la refactorización #3

**Efecto medible**

| Métrica | Antes | Después |
|---------|-------|---------|
| `pytest` | 20/20 | 20/20 |
| `ruff check src` | 15 errores | 12 errores |
| Líneas en `src/` | — | ~25 menos |

Errores de ruff cerrados: `N802` (`reporteViejoCSV` no era snake_case), `SIM115`
(ese mismo archivo abría un CSV sin `with`) y `F401` (`os` importado sin usar).
Vale la pena notarlo: **borrar la función resolvió dos advertencias que, de otro
modo, habrían costado una refactorización entera**. Antes de arreglar código
conviene preguntarse si ese código debe existir.

**Verificación previa.** Se buscó cada nombre en todo el proyecto (`src/` y
`tests/`) y los cuatro aparecían únicamente en su propia definición, con cero
llamadas. `MODO_DEBUG` tampoco se persiste en el JSON: `almacen.guardar_datos`
solo escribe inventario, ventas y contador.

### Detalle de la refactorización #4

**Efecto medible**

| Métrica | Antes | Después |
|---------|-------|---------|
| `pytest` | 20/20 | 20/20 |
| `ruff check src` | 12 errores | 12 errores |
| Literales mágicos en `src/` | 15 apariciones | 0 |
| Lugares donde vive el umbral de stock bajo | 2 | 1 |

Esta refactorización **no cierra ningún error de ruff**, y eso es esperable: el
linter no tiene forma de saber que `0.16` es una tasa de IVA. Es un buen
recordatorio de que *pasar el linter* y *tener código legible* son objetivos
distintos, y que el primero no implica el segundo.

**Dónde viven las constantes.** Se colocaron en `gestor.py`, no en `reportes.py`,
aunque `STOCK_MINIMO` y `DECIMALES_MONEDA` se consuman desde allí. El criterio es
que son reglas de negocio, no decisiones de presentación: `reportes.py` ya
importa `gestor` y ahora las referencia como `gestor.STOCK_MINIMO`. Así el
reporte y la alerta de inventario no pueden volver a desincronizarse.

**Validación de equivalencia.** Se volvió a correr el barrido de 8 569
combinaciones contra la fórmula original: resultado idéntico. Además se verificó
con una búsqueda por expresión regular que no quedara ningún literal mágico
suelto en `src/`.

**Validación de equivalencia.** La suite solo ejerce cuatro montos concretos, así
que para comprobar que el comportamiento observable no cambió se comparó la
fórmula original contra la refactorizada en un barrido de **8 569 combinaciones**
de precio, cantidad y código de cliente — incluyendo los bordes exactos de 500 y
1000, y clientes `""`, `None`, `"VI"`, `"VIP"`, `"vip001"` y `"XVIP1"`. Resultado:
**idéntico en los cuatro campos** (subtotal, descuento, impuesto y total).

**Decisiones de diseño y riesgos evitados**

- `cotizar` **no** aplica el extra VIP porque nunca recibió un código de cliente.
  Por eso `calcular_importes` declara `cliente=""` como parámetro opcional: si se
  hubiera hecho obligatorio o se hubiera asumido un cliente por defecto distinto,
  las cotizaciones habrían cambiado de valor.
- Los importes se devuelven **sin redondear** salvo `total`, replicando el
  original: `registrar_venta` redondea al guardar cada campo. Redondear dentro de
  la función habría alterado la condición `if descuento > 0` que decide si el
  ticket imprime la línea de descuento.
- `cliente[0:3] == "VIP"` precedido de `len(cliente) >= 3` se sustituyó por
  `cliente.startswith("VIP")`: el chequeo de longitud era redundante, porque un
  texto más corto nunca puede ser igual a `"VIP"`.
- **No se introdujeron constantes con nombre** para `1000`, `500`, `0.16`, etc.
  Esa es una refactorización distinta y merece su propio commit; mezclarla aquí
  habría roto la atomicidad del cambio.

## Reflexión final (10-15 líneas)

Responde: ¿Qué tan útil fue Claude Code para detectar y corregir los problemas?
¿Qué propuso la IA que tú no habías notado? ¿En qué casos tuviste que corregir
o rechazar sus sugerencias? ¿Qué aprendiste sobre refactorizar con apoyo de IA?

*(Escribe aquí tu reflexión)*
