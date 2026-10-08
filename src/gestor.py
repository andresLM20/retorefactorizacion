# -*- coding: utf-8 -*-
"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime
from typing import NamedTuple

# ---------------------------------------------------------------
# Reglas de negocio de la tienda
# ---------------------------------------------------------------
# Descuento por volumen de compra: se aplica sobre el subtotal.
MONTO_DESCUENTO_ALTO = 1000
TASA_DESCUENTO_ALTO = 0.10
MONTO_DESCUENTO_MEDIO = 500
TASA_DESCUENTO_MEDIO = 0.05

# Extra para clientes VIP, solo si la compra ya con descuento supera el minimo.
PREFIJO_CLIENTE_VIP = "VIP"
MONTO_MINIMO_VIP = 200
TASA_DESCUENTO_VIP = 0.02

TASA_IVA = 0.16

# Un producto se considera en riesgo cuando baja de esta cantidad de unidades.
STOCK_MINIMO = 5

# Los importes se manejan en pesos y centavos.
DECIMALES_MONEDA = 2

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO = {}
VENTAS = []
contadorVentas = 0
ultimo_error = ""


def reiniciar_sistema():
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contadorVentas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contadorVentas = 0
    ultimo_error = ""


def agregarProducto(codigo, nombre, precio, stock):
    # valida los datos y da de alta un producto en el inventario
    global ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return False
    if codigo in INVENTARIO:
        ultimo_error = "el producto ya existe"
        return False
    if precio <= 0:
        ultimo_error = "precio invalido"
        return False
    if stock < 0:
        ultimo_error = "stock invalido"
        return False
    x = {}
    x["codigo"] = codigo
    x["nombre"] = nombre
    x["precio"] = precio
    x["stock"] = stock
    INVENTARIO[codigo] = x
    return True


def eliminar_producto(codigo):
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo, cantidad):
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    aux = INVENTARIO[codigo]["stock"] + cantidad
    if aux < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = aux
    return True


def buscarProducto(texto):
    # busca productos cuyo nombre contenga el texto (sin importar mayusculas)
    temp2 = []
    for k in INVENTARIO:
        if texto.lower() in INVENTARIO[k]["nombre"].lower():
            temp2.append(INVENTARIO[k])
    return temp2


class ImportesVenta(NamedTuple):
    """Desglose economico de una compra.

    Los tres primeros valores van sin redondear; `total` ya viene redondeado
    a 2 decimales, que es la precision con la que se cobra.
    """

    subtotal: float
    descuento: float
    impuesto: float
    total: float


def _descuento_por_volumen(subtotal):
    """Descuento que corresponde al monto de la compra."""
    if subtotal >= MONTO_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= MONTO_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0


def _descuento_extra_vip(subtotal, descuento, cliente):
    """Extra para clientes VIP, solo si la compra ya con descuento es grande."""
    if not cliente or not cliente.startswith(PREFIJO_CLIENTE_VIP):
        return 0
    if subtotal - descuento <= MONTO_MINIMO_VIP:
        return 0
    return subtotal * TASA_DESCUENTO_VIP


def calcular_importes(precio, cantidad, cliente=""):
    """Calcula subtotal, descuentos, IVA y total de una compra.

    Es la unica fuente de verdad del calculo: la usan tanto `registrar_venta`
    como `cotizar`, de modo que una cotizacion siempre coincide con lo que se
    termina cobrando.
    """
    subtotal = precio * cantidad
    descuento = _descuento_por_volumen(subtotal)
    descuento = descuento + _descuento_extra_vip(subtotal, descuento, cliente)
    base = subtotal - descuento
    impuesto = base * TASA_IVA
    return ImportesVenta(
        subtotal=subtotal,
        descuento=descuento,
        impuesto=impuesto,
        total=round(base + impuesto, DECIMALES_MONEDA),
    )


def registrar_venta(codigo, cantidad, cliente=""):
    """Registra una venta completa.

    Valida los datos, delega el calculo a `calcular_importes`, descuenta el
    stock, genera el folio, arma el ticket en texto y guarda el registro en
    la lista de ventas. Si algo falla regresa None y deja el motivo en
    ultimo_error.
    """
    global contadorVentas, ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return None
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    producto = INVENTARIO[codigo]
    if producto["stock"] < cantidad:
        ultimo_error = "stock insuficiente"
        return None

    importes = calcular_importes(producto["precio"], cantidad, cliente)
    # descontar del inventario
    producto["stock"] = producto["stock"] - cantidad
    contadorVentas = contadorVentas + 1
    venta = {}
    venta["folio"] = contadorVentas
    venta["codigo"] = codigo
    venta["nombre"] = producto["nombre"]
    venta["cantidad"] = cantidad
    venta["subtotal"] = round(importes.subtotal, DECIMALES_MONEDA)
    venta["descuento"] = round(importes.descuento, DECIMALES_MONEDA)
    venta["impuesto"] = round(importes.impuesto, DECIMALES_MONEDA)
    venta["total"] = importes.total
    venta["cliente"] = cliente
    venta["fecha"] = datetime.now().strftime(FORMATO_FECHA)
    # armar el ticket en texto plano
    t = ""
    t = t + "TIENDA LA ESQUINA\n"
    t = t + "----------------------------\n"
    t = t + "Folio: " + str(venta["folio"]) + "\n"
    t = t + venta["nombre"] + " x" + str(cantidad) + "\n"
    t = t + "Subtotal: $" + str(venta["subtotal"]) + "\n"
    if importes.descuento > 0:
        t = t + "Descuento: -$" + str(venta["descuento"]) + "\n"
    t = t + "IVA: $" + str(venta["impuesto"]) + "\n"
    t = t + "TOTAL: $" + str(venta["total"]) + "\n"
    venta["ticket"] = t
    VENTAS.append(venta)
    return venta


def cotizar(codigo, cantidad):
    """Calcula cuanto costaria una compra sin registrar la venta."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    return calcular_importes(INVENTARIO[codigo]["precio"], cantidad).total
