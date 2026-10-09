# -*- coding: utf-8 -*-
"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os

import gestor


def guardar_datos(ruta):
    """Guarda el inventario, las ventas y el folio actual en un JSON."""
    d = {}
    d["inventario"] = gestor.INVENTARIO
    d["ventas"] = gestor.VENTAS
    d["contador"] = gestor.contadorVentas
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
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
            d = json.load(f)
        except Exception:
            gestor.ultimo_error = "archivo corrupto"
            return False
    gestor.INVENTARIO.clear()
    for k in d["inventario"]:
        gestor.INVENTARIO[k] = d["inventario"][k]
    gestor.VENTAS.clear()
    for v in d["ventas"]:
        gestor.VENTAS.append(v)
    gestor.contadorVentas = d.get("contador", 0)
    return True


def hayArchivo(ruta):
    # checa si ya existe el archivo de datos
    if os.path.exists(ruta):
        return True
    else:
        return False
