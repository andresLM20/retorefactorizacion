# CLAUDE.md — Gestor de inventario y ventas "La Esquina"

Contexto para Claude Code al trabajar en este repositorio.

## Qué es este proyecto

Aplicación de consola en Python (3.10+) que administra el inventario y las
ventas de una tienda pequeña: alta de productos, registro de ventas con
descuentos e IVA, cotizaciones, alertas de stock bajo, reporte de más vendidos
y persistencia en JSON.

**Este es un ejercicio de refactorización.** El programa ya funciona y todas
las pruebas pasan. El código está deliberadamente mal escrito: funciones
gigantes, lógica duplicada, nombres crípticos (`temp2`, `aux`, `hacer_cosa`),
números mágicos, estado global, código muerto, anidamiento excesivo y estilos
de nombrado mezclados. El objetivo es **mejorar el código sin cambiar su
comportamiento observable**.

## Estructura

```
src/
├── gestor.py      # Lógica de negocio: productos, ventas, descuentos, IVA
├── almacen.py     # Persistencia: guardar/cargar JSON
├── reportes.py    # Reportes: inventario, resumen de ventas, más vendidos
└── main.py        # Menú interactivo de consola (único módulo con I/O de usuario)
tests/             # Suite pytest de caja negra — NO MODIFICAR
pyproject.toml     # Configuración de ruff y pytest — NO MODIFICAR
datos_ejemplo.json # Datos de ejemplo; main.py lo lee y lo reescribe al salir
```

`src/` **no es un paquete**. `tests/conftest.py` hace `sys.path.insert` de
`src/`, por lo que los módulos se importan planos: `import gestor`,
`import almacen`, `import reportes`. No conviertas esto a imports de paquete
(`from src.gestor import ...`) ni agregues `__init__.py`: rompe la suite.

## Comandos

```bash
# Entorno (una sola vez)
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

pytest                           # Suite completa — deben pasar TODAS
pytest tests/test_gestor.py -v   # Un archivo
ruff check src                   # Linter — meta final: 0 errores
ruff check src --fix             # Solo corrige lo trivial
cd src && python main.py         # App interactiva
```

**Después de CADA refactorización corre `pytest` y `ruff check src`.** No
encadenes varios cambios antes de validar.

## Reglas que debes respetar

1. **No modifiques `tests/`.** Si una prueba falla, el error está en la
   refactorización, no en la prueba. Nunca ajustes un test para que pase.
2. **No modifiques `pyproject.toml`.** Cada regla de ruff activada corresponde
   a un code smell real del proyecto. Bajar `max-complexity` o quitar reglas es
   hacer trampa y se revisa en el PR.
3. **El comportamiento observable no cambia.** Mismos valores de retorno,
   mismas condiciones de error, mismo formato de ticket y de reportes.
4. **No renombres la API que consumen los tests** (ver abajo).
5. **Un cambio a la vez**, con su commit atómico y su entrada en la bitácora.
6. **No agregues dependencias.** Solo `pytest` y `ruff`; la app usa biblioteca
   estándar.

## API pública intocable

Los tests llaman estos nombres directamente. Renombrarlos rompe la suite:

| Módulo | Nombres |
|--------|---------|
| `gestor` | `agregarProducto`, `buscarProducto`, `eliminar_producto`, `actualizar_stock`, `registrar_venta`, `cotizar`, `reiniciar_sistema` |
| `gestor` (estado) | `INVENTARIO` (dict), `VENTAS` (list) |
| `almacen` | `guardar_datos`, `cargar_datos` |
| `reportes` | `productos_stock_bajo`, `total_vendido`, `mas_vendidos`, `reporte_inventario` |

`agregarProducto` y `buscarProducto` conservan su camelCase a propósito: están
en `ignore-names` de ruff porque los tests los usan.

`INVENTARIO` y `VENTAS` deben seguir existiendo como atributos de módulo con
esos nombres, y `reiniciar_sistema()` debe vaciarlos **in-place** (`.clear()`),
porque el fixture `sistema_limpio` de `conftest.py` corre antes y después de
cada prueba. Se puede reducir el estado global, pero esa fachada se mantiene.

Nombres que **sí** se pueden cambiar libremente (solo los usa `main.py`, que
también es tuyo): `hayArchivo`, `hacer_cosa`, `resumen_ventas`, `pedir_numero`,
`ultimo_error`, `contadorVentas`, `MODO_DEBUG`.

## Reglas de negocio fijadas por los tests

Verificadas con valores exactos — cualquier refactorización debe preservarlas:

- **Descuento por volumen** sobre el subtotal: `>= $1000` → 10%; `>= $500` →
  5%; menos → 0%.
- **Extra VIP**: si el código de cliente empieza con `VIP` **y** el subtotal ya
  con descuento supera $200, se suma un 2% del subtotal al descuento.
- **IVA del 16%** sobre la base (subtotal − descuento).
- **Total redondeado a 2 decimales.**
- `cotizar(codigo, cantidad)` debe dar **exactamente** el mismo total que
  `registrar_venta` para la misma compra (hay un test que lo compara). Es la
  duplicación más evidente del proyecto y la candidata natural a extraerse a
  una sola función de cálculo.
- **Stock bajo** = menos de 5 unidades.
- Una venta fallida **no** debe tocar el stock ni agregar nada a `VENTAS`.
- Los folios son consecutivos empezando en 1.

## Code smells conocidos (candidatos a refactorización)

- `registrar_venta` en [src/gestor.py](src/gestor.py) hace todo: valida,
  calcula, descuenta stock, genera folio, arma el ticket y persiste. Tiene 4
  niveles de `if` anidados solo para validar.
- Cálculo de descuento + IVA duplicado entre `registrar_venta` y `cotizar`.
- Números mágicos: `1000`, `500`, `0.10`, `0.05`, `0.02`, `200`, `0.16`, `5`.
- Nombres sin significado: `temp2`, `aux`, `x`, `t`, `d`, `s`, `p`,
  `hacer_cosa`.
- Código muerto: `calcular_descuento_viejo`, `reporteViejoCSV`, `MODO_DEBUG`,
  la función `exportar_txt` comentada.
- Archivos abiertos sin `with` en `almacen.py` y `reportes.py`.
- Bubble sort manual en `mas_vendidos` pudiendo usar `sorted`.
- `hayArchivo` es un `if/else` que devuelve `True`/`False`.
- Manejo de errores por variable global `ultimo_error` en vez de excepciones.
- Concatenación de strings en bucles para armar reportes.
- `reporte_inventario` y `resumen_ventas` mezclan construcción del texto con
  `print` (lógica e I/O acopladas).
- Sin type hints en ningún módulo.

## Entrega

Trabajo en la rama `refactorizacion`, PR hacia `main`, commits atómicos (uno
por refactorización) y `BITACORA.md` (copia de `BITACORA_TEMPLATE.md`) con el
prompt usado, el cambio, su justificación y el resultado de los tests en cada
paso.
