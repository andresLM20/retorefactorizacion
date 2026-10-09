"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

import almacen
import gestor
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje):
    # pide un numero al usuario hasta que escriba algo valido
    while True:
        respuesta = input(mensaje)
        try:
            return float(respuesta)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def _alta_de_producto():
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = int(pedir_numero("Stock inicial: "))
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        print("Error:", gestor.ultimo_error)


def _venta():
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is not None:
        print(venta["ticket"])
    else:
        print("Error:", gestor.ultimo_error)


def _cotizacion():
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    total = gestor.cotizar(codigo, cantidad)
    if total is not None:
        print("Total estimado (con IVA): $" + str(total))
    else:
        print("Error:", gestor.ultimo_error)


def _reporte_inventario():
    # Envuelta a proposito: reporte_inventario regresa el texto del reporte y
    # ninguna accion del menu debe regresar un valor, porque eso lo cerraria.
    reportes.reporte_inventario()


def _resumen_ventas():
    reportes.resumen_ventas()


def _mas_vendidos():
    for codigo, unidades in reportes.mas_vendidos():
        print(codigo, "->", unidades, "unidades")


def _alertas_stock_bajo():
    bajos = reportes.productos_stock_bajo()
    if not bajos:
        print("No hay productos con stock bajo.")
        return
    for producto in bajos:
        print("OJO:", producto["nombre"], "solo tiene", producto["stock"], "unidades")


def _guardar_y_salir():
    """Unica opcion que termina el menu: regresa True para cortar el bucle."""
    almacen.guardar_datos(ARCHIVO)
    print("Datos guardados. Hasta luego.")
    return True


# Cada entrada es la etiqueta que ve el usuario y la accion que la atiende.
# Una accion que regresa True termina el menu.
OPCIONES = {
    "1": ("Agregar producto", _alta_de_producto),
    "2": ("Registrar venta", _venta),
    "3": ("Cotizar", _cotizacion),
    "4": ("Reporte de inventario", _reporte_inventario),
    "5": ("Resumen de ventas", _resumen_ventas),
    "6": ("Mas vendidos", _mas_vendidos),
    "7": ("Alertas de stock bajo", _alertas_stock_bajo),
    "8": ("Guardar y salir", _guardar_y_salir),
}


def _mostrar_opciones():
    print("")
    for clave, (etiqueta, _) in OPCIONES.items():
        print(clave + ") " + etiqueta)


def _cargar_datos_previos():
    if almacen.hay_archivo(ARCHIVO):
        almacen.cargar_datos(ARCHIVO)
        print("Datos cargados de", ARCHIVO)


def menu():
    """Bucle principal: muestra las opciones y despacha la que elija el usuario."""
    print("Bienvenido al gestor de la tienda La Esquina")
    _cargar_datos_previos()
    while True:
        _mostrar_opciones()
        opcion = OPCIONES.get(input("Opcion: "))
        if opcion is None:
            print("Opcion no valida.")
            continue
        _, accion = opcion
        if accion() is True:
            break


if __name__ == "__main__":
    menu()
