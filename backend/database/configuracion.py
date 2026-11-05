"""Valores ajustables compartidos por la consola, el servicio y la web."""

import json
from pathlib import Path


RUTA_CONFIG = Path(__file__).resolve().parent.parent / "configuracion.json"


def cargar_configuracion(ruta=RUTA_CONFIG):
    with Path(ruta).open(encoding="utf-8") as archivo:
        config = json.load(archivo)
    if not isinstance(config, dict):
        raise ValueError("La configuración debe ser un objeto JSON")
    limites = {
        "puerto": (1, 65535),
        "plazo_dias": (1, None),
        "multa_diaria_centavos": (0, None),
        "filas_por_pagina": (1, None),
        "espera_busqueda_ms": (0, None),
        "tiempo_solicitud_ms": (1, None),
        "duracion_aviso_ms": (1, None),
    }
    for nombre, (minimo, maximo) in limites.items():
        valor = config.get(nombre)
        if type(valor) is not int or valor < minimo or (maximo is not None and valor > maximo):
            raise ValueError(f"Configuración inválida: {nombre}")
    for nombre in ("base_datos", "idioma", "moneda"):
        if not isinstance(config.get(nombre), str) or not config[nombre].strip():
            raise ValueError(f"Configuración inválida: {nombre}")
    return config


CONFIG = cargar_configuracion()
