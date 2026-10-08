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
