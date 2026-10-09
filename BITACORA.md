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

| 5  | «Sí, continúa.» (guard clauses en la validación de `registrar_venta`) | Se aplanó la pirámide de 4 `if` anidados de la entrada de `registrar_venta` convirtiéndola en cuatro guard clauses consecutivas, cada una con su mensaje de error y su `return None`. Desapareció la variable `temp2 = None`, que solo existía para cargar el producto desde el fondo del anidamiento; ahora el producto se obtiene con `producto = INVENTARIO[codigo]` una vez superadas las validaciones. | El patrón anidado obligaba a leer la función de adentro hacia afuera: el caso exitoso estaba cuatro niveles adentro y los errores quedaban en los `else`, lejos de la condición que los provocaba. Con guard clauses cada regla de rechazo se lee en dos líneas contiguas —condición y consecuencia— y el cuerpo real de la función queda al nivel base, sin indentación. También elimina la variable centinela `temp2 = None`, que era un residuo del anidamiento. | 20/20 ✔ |

| 6  | «Sí.» (partir `registrar_venta` extrayendo la construcción del registro y del ticket) | Se extrajeron dos funciones de `registrar_venta`: `_construir_registro_venta`, que arma el diccionario que se guarda en `VENTAS` con los importes ya redondeados, y `_generar_ticket`, que produce el texto del comprobante. El ticket pasó de nueve concatenaciones sucesivas sobre una variable `t` a una lista de líneas unida con `"\n".join(...)`. `registrar_venta` quedó como orquestador: valida, calcula, aplica efectos y delega. | `registrar_venta` seguía haciendo tres trabajos de naturaleza distinta: reglas de negocio (descontar stock, asignar folio), estructura de datos (armar el registro) y **presentación** (formatear un ticket para imprimir). Mezclar presentación con lógica de negocio es el acoplamiento más caro del módulo: cambiar el diseño del comprobante obligaba a editar la función que mueve el inventario, con el riesgo de romper una venta por tocar un texto. Ahora el formato del ticket vive en un solo lugar y se puede cambiar sin entrar al flujo de la venta. | 20/20 ✔ |

| 7  | «Sigamos hasta dejar el linter en cero.» (descomponer `menu()`) | Se partió `menu()` —una cadena de 8 `elif` que mezclaba presentación, lectura de entrada y orquestación— en un handler por opción (`_alta_de_producto`, `_venta`, `_cotizacion`, `_reporte_inventario`, `_resumen_ventas`, `_mas_vendidos`, `_alertas_stock_bajo`, `_guardar_y_salir`) más una tabla de despacho `OPCIONES` que asocia cada tecla con su etiqueta y su acción. El menú en pantalla ahora se genera recorriendo esa tabla, así que agregar una opción es añadir una entrada en un solo lugar. | `menu()` era la función más compleja del proyecto (17, con el límite en 10). La cadena de `elif` obligaba a mantener sincronizados tres sitios separados: el `print` de la etiqueta, la comparación de la tecla y el cuerpo que la atiende; agregar una opción significaba tocar los tres y nada avisaba si uno se olvidaba. Con la tabla de despacho, etiqueta y acción viven juntas y la pantalla se deriva de la misma fuente, de modo que no pueden desincronizarse. | 20/20 ✔ |

| 8  | (continuación del mismo plan) Manejo de archivos con `with` en `almacen.py` | `guardar_datos` y `cargar_datos` abrían el archivo con `open(...)` y lo cerraban con un `f.close()` manual. Se sustituyeron por bloques `with`, que cierran el descriptor pase lo que pase. De paso se eliminó el modo `"r"` redundante y el `f.close()` duplicado del camino de error. | El `close()` manual solo se ejecuta si el flujo llega hasta él: cualquier excepción entre el `open` y el `close` deja el descriptor colgado. En `guardar_datos` el riesgo era real porque `json.dump` no estaba protegido por ningún `try`. Se comprobó experimentalmente (ver detalle) que, con el código anterior, un fallo de serialización podía dejar el archivo de datos bloqueado. | 20/20 ✔ |

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

### Detalle de la refactorización #5

**Efecto medible**

| Métrica | Antes | Después |
|---------|-------|---------|
| `pytest` | 20/20 | 20/20 |
| `ruff check src` | 12 errores | 12 errores |
| Profundidad de anidamiento en la validación | 4 niveles | 1 nivel |
| Complejidad ciclomática de `registrar_venta` | 6 | 6 |
| Variables centinela | `temp2 = None` | ninguna |

**La complejidad ciclomática no bajó, y es correcto que no lo haga.** Se midió
con `ruff --select C901 --config "lint.mccabe.max-complexity=1"` (sin modificar
`pyproject.toml`) antes y después: 6 en ambos casos. Aplanar anidamiento no
cambia el número de caminos de ejecución, solo la profundidad a la que hay que
leerlos. La métrica que mejora es el anidamiento, y esa McCabe no la mide. Es un
ejemplo claro de que una refactorización puede ser valiosa sin mover ni una
métrica automática.

**Validación del orden de las reglas.** Este cambio invierte cuatro condiciones
booleanas (`codigo is not None and codigo != ""` pasa a `codigo is None or
codigo == ""`, etc.), que es justo donde se cuelan los errores de signo. Además,
el **orden** de las validaciones determina qué mensaje queda en `ultimo_error`
cuando una entrada viola varias reglas a la vez. Se comparó la pirámide original
contra las guard clauses en **66 combinaciones** de código y cantidad —incluyendo
`None`, `""`, el entero `0`, cantidades negativas y un producto con stock 0—
verificando en cada caso el mensaje de error exacto y que una venta rechazada no
dejara efectos laterales en el stock ni en `VENTAS`. Resultado: idéntico.

### Detalle de la refactorización #6

**Efecto medible**

| Métrica | Antes | Después |
|---------|-------|---------|
| `pytest` | 20/20 | 20/20 |
| `ruff check src` | 12 errores | 12 errores |
| Cuerpo de `registrar_venta` | 30 líneas | 11 líneas |
| Complejidad de `registrar_venta` | 6 | 5 |
| Responsabilidades en `registrar_venta` | 3 | 1 (orquestar) |

**Validación byte a byte del ticket.** El ticket es una cadena que el menú
imprime tal cual, así que cualquier diferencia de un espacio o un salto de línea
sería un cambio de comportamiento observable. Para comprobarlo se cargó el
`gestor.py` del commit anterior como **módulo paralelo** (vía `importlib`) y se
ejecutaron ambas versiones sobre los mismos 10 escenarios —sin descuento, con
descuento medio y alto, con y sin cliente VIP, un VIP bajo el mínimo y un
producto con nombre largo—, comparando el ticket carácter por carácter.
Resultado: idéntico.

**También se comparó el orden de las claves del diccionario**, no solo sus
valores. Importa porque `almacen.guardar_datos` serializa `VENTAS` a JSON y los
diccionarios de Python conservan el orden de inserción: reordenar las claves
habría cambiado el archivo de datos generado, aunque ninguna prueba lo detectara.

**Detalle de diseño.** `_generar_ticket` recibe `mostrar_descuento` como
parámetro aparte en vez de deducirlo del registro. La razón es sutil: la decisión
de imprimir la línea de descuento depende del descuento **sin redondear**,
mientras que el registro guarda el redondeado. Deducirlo dentro de la función
habría cambiado el comportamiento para descuentos menores a medio centavo.

### Detalle de la refactorización #7

**Efecto medible**

| Métrica | Antes | Después |
|---------|-------|---------|
| `pytest` | 20/20 | 20/20 |
| `ruff check src` | 12 errores | 11 errores |
| Complejidad de `menu` | **17** | **4** |
| Cuerpo de `menu` | 58 líneas | 11 líneas |
| Lugares a tocar para agregar una opción | 3 | 1 |

Con esto se cierra el último `C901` del proyecto: ninguna función supera ya el
límite de complejidad.

**Un bug que la refactorización estuvo a punto de introducir.** El diseño natural
de una tabla de despacho es `if accion(): break`, usando el valor de retorno del
handler para decidir si el menú termina. Pero `reportes.reporte_inventario` y
`reportes.resumen_ventas` **devuelven el texto del reporte** además de
imprimirlo, y una cadena no vacía es «verdadera» en Python: el menú se habría
cerrado solo al pedir un reporte. Se corrigió envolviendo ambas en handlers que
no devuelven nada y comparando con `is True` en vez de confiar en la
«verdadez» del valor. Es un recordatorio de que una función que *hace algo* y
además *devuelve algo* es peligrosa cuando se la trata como intercambiable con
otras.

**Validación sin red de seguridad.** `main.py` no tiene ninguna prueba: la suite
cubre `gestor`, `almacen` y `reportes`, pero no el menú. Para no refactorizar a
ciegas se construyó un arnés que ejecuta la versión anterior y la nueva con la
**misma secuencia de entradas simuladas** (parcheando `input`) y compara la
salida completa carácter por carácter, además del JSON que queda guardado al
salir. Se probaron **16 guiones**: alta de producto válida e inválida, producto
duplicado, venta normal, venta VIP, venta sin stock, producto inexistente,
cotización válida e inválida, los cuatro reportes, opción inexistente, un número
mal escrito y un recorrido largo que encadena 17 interacciones. Resultado:
idéntico en los 16.

### Detalle de la refactorización #8

**Efecto medible**

| Métrica | Antes | Después |
|---------|-------|---------|
| `pytest` | 20/20 | 20/20 |
| `ruff check src` | 11 errores | 8 errores |
| Archivos abiertos sin `with` | 2 | 0 |

Errores cerrados: los dos `SIM115` y el `UP015` (modo `"r"` redundante).

**Se intentó demostrar el bug y al principio no apareció.** La primera prueba
—forzar un `TypeError` dentro de `json.dump` y comprobar si el archivo quedaba
bloqueado— dio el mismo resultado en ambas versiones: el archivo se cerraba
bien. La razón es que CPython usa conteo de referencias: al propagarse la
excepción se destruye el *frame* de la función, con él la variable local `f`, y
el archivo se cierra solo. El `close()` manual estaba siendo rescatado por un
detalle de implementación del intérprete.

**Pero sí hay un caso donde falla.** Si el código que llama **retiene el
traceback** —exactamente lo que hace cualquier manejador que registre el error
para diagnosticarlo después—, el frame sigue vivo, `f` no se libera y el archivo
queda abierto. Repitiendo la prueba con la excepción guardada en una variable, el
resultado fue:

```
ANTES  (sin with): DESCRIPTOR COLGADO, el archivo sigue abierto
DESPUES (con with): el archivo se cerro correctamente
```

En Windows eso significa que `datos_ejemplo.json` queda bloqueado y no se puede
reemplazar ni borrar hasta que termine el proceso. La lección no es solo que
`with` sea mejor estilo: es que el código anterior dependía, sin saberlo, de un
comportamiento que el lenguaje no garantiza.

**Decisión de diseño.** En `cargar_datos` el `open` se dejó **fuera** del `try`,
igual que en el original. Meterlo dentro habría sido más corto, pero habría
cambiado el comportamiento: un archivo que existe pero no se puede abrir (por
permisos, o porque otro proceso lo tiene tomado) habría pasado a reportarse como
«archivo corrupto» en vez de propagar el error real.

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
