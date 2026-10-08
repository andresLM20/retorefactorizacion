# -*- coding: utf-8 -*-
"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime
from typing import NamedTuple

# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO = {}
VENTAS = []
contadorVentas = 0
ultimo_error = ""
MODO_DEBUG = False


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
    if subtotal >= 1000:
        return subtotal * 0.10
    if subtotal >= 500:
        return subtotal * 0.05
    return 0


def _descuento_extra_vip(subtotal, descuento, cliente):
    """Extra para clientes VIP, solo si la compra ya con descuento es grande."""
    if not cliente or not cliente.startswith("VIP"):
        return 0
    if subtotal - descuento <= 200:
        return 0
    return subtotal * 0.02


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
    impuesto = base * 0.16
    return ImportesVenta(
        subtotal=subtotal,
        descuento=descuento,
        impuesto=impuesto,
        total=round(base + impuesto, 2),
    )


def registrar_venta(codigo, cantidad, cliente=""):
    """Registra una venta completa.

    Valida los datos, delega el calculo a `calcular_importes`, descuenta el
    stock, genera el folio, arma el ticket en texto y guarda el registro en
    la lista de ventas. Si algo falla regresa None y deja el motivo en
    ultimo_error.
    """
    global contadorVentas, ultimo_error
    temp2 = None
    if codigo is not None and codigo != "":
        if codigo in INVENTARIO:
            if cantidad is not None and cantidad > 0:
                if INVENTARIO[codigo]["stock"] >= cantidad:
                    temp2 = INVENTARIO[codigo]
                else:
                    ultimo_error = "stock insuficiente"
                    return None
            else:
                ultimo_error = "cantidad invalida"
                return None
        else:
            ultimo_error = "producto no existe"
            return None
    else:
        ultimo_error = "codigo vacio"
        return None
    importes = calcular_importes(temp2["precio"], cantidad, cliente)
    # descontar del inventario
    temp2["stock"] = temp2["stock"] - cantidad
    contadorVentas = contadorVentas + 1
    venta = {}
    venta["folio"] = contadorVentas
    venta["codigo"] = codigo
    venta["nombre"] = temp2["nombre"]
    venta["cantidad"] = cantidad
    venta["subtotal"] = round(importes.subtotal, 2)
    venta["descuento"] = round(importes.descuento, 2)
    venta["impuesto"] = round(importes.impuesto, 2)
    venta["total"] = importes.total
    venta["cliente"] = cliente
    venta["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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


def calcular_descuento_viejo(monto):
    # NOTA: esta era la formula de descuentos que se uso hasta 2023,
    # ya nadie la llama pero la dejamos por si acaso
    if monto > 800:
        return monto * 0.08
    return 0


# def exportar_txt(ruta):
#     f = open(ruta, "w")
#     for k in INVENTARIO:
#         f.write(k + " - " + str(INVENTARIO[k]["stock"]) + "\n")
#     f.close()
#     return True
