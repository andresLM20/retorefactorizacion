# -*- coding: utf-8 -*-
"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os

import gestor


def guardar_datos(ruta):
    """Guarda el inventario, las ventas y el folio actual en un JSON."""
    datos = {
        "inventario": gestor.INVENTARIO,
        "ventas": gestor.VENTAS,
        "contador": gestor.contador_ventas,
    }
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    return True


def cargar_datos(ruta):
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe o esta corrupto.
    """
    if not os.path.exists(ruta):
        gestor.ultimo_error = "el archivo no existe"
        return False
    # El open queda fuera del try a proposito: solo se considera "corrupto" un
    # archivo que no se puede interpretar como JSON, no uno que no se puede
    # abrir. Un error al abrirlo sigue propagandose, como antes.
    with open(ruta, encoding="utf-8") as f:
        try:
            datos = json.load(f)
        except Exception:
            gestor.ultimo_error = "archivo corrupto"
            return False
    # Se vacian y rellenan en el lugar, sin reasignar: otros modulos y el
    # fixture de las pruebas guardan una referencia a estas mismas colecciones.
    gestor.INVENTARIO.clear()
    gestor.INVENTARIO.update(datos["inventario"])
    gestor.VENTAS.clear()
    gestor.VENTAS.extend(datos["ventas"])
    gestor.contador_ventas = datos.get("contador", 0)
    return True


def hay_archivo(ruta):
    """Indica si ya existe el archivo de datos."""
    return os.path.exists(ruta)
