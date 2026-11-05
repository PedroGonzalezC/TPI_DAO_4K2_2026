"""Interfaz de consola: python -m backend --help."""

import argparse
import json

from .services.servicio import Biblioteca, ReglaNegocio
from .database.configuracion import CONFIG
from .models.modelo import CONDICIONES_DEVOLUCION
from .services.operaciones import ejecutar


def construir_parser():
    parser = argparse.ArgumentParser(description="Red de bibliotecas: préstamos interbibliotecarios")
    parser.add_argument("--db", default=CONFIG["base_datos"], help="Archivo SQLite")
    sub = parser.add_subparsers(dest="comando", required=True)

    def comando(nombre, accion, *campos):
        p = sub.add_parser(nombre)
        p.set_defaults(accion=accion)
        for campo, tipo in campos:
            p.add_argument(campo, type=tipo)
        return p

    comando("sede-crear", "crear_sede", ("nombre", str), ("direccion", str), ("contacto", str), ("horarios", str))
    p = comando("sede-editar", "editar_sede", ("id", int))
    for campo in ("direccion", "contacto", "horarios"):
        p.add_argument(f"--{campo}")
    p.add_argument("--activa", type=int, choices=(0, 1))
    comando("socio-crear", "crear_socio", ("documento", str), ("nombre", str), ("email", str))
    p = comando("socio-editar", "editar_socio", ("id", int))
    p.add_argument("--nombre")
    p.add_argument("--email")
    p.add_argument("--habilitado", type=int, choices=(0, 1))
    p = comando("libro-crear", "crear_libro", ("isbn", str), ("titulo", str), ("autor", str))
    p.add_argument("--anio", type=int)
    p = comando("libro-editar", "editar_libro", ("id", int))
    p.add_argument("--titulo")
    p.add_argument("--autor")
    p.add_argument("--anio", type=int)
    comando("ejemplar-crear", "crear_ejemplar", ("codigo", str), ("libro_id", int), ("sede_id", int))
    comando("listar", "listar", ("tabla", str))
    p = comando("disponibilidad", "disponibilidad")
    p.add_argument("--sede", type=int)
    comando("reserva-crear", "reservar", ("socio_id", int), ("libro_id", int), ("sede_id", int))
    comando("reserva-cancelar", "cancelar_reserva", ("id", int))
    comando("prestamo-solicitar", "solicitar_prestamo", ("socio_id", int), ("ejemplar_id", int),
            ("sede_origen_id", int), ("sede_destino_id", int))
    comando("prestamo-entregar", "entregar_prestamo", ("id", int))
    p = comando("prestamo-devolver", "devolver_prestamo", ("id", int))
    p.add_argument("--condicion", choices=CONDICIONES_DEVOLUCION, default="BUENO")
    p = comando("remito-avanzar", "avanzar_remito", ("id", int), ("estado", str))
    p.add_argument("--detalle", default="")
    comando("remito-historial", "historial_remito", ("id", int))
    p = comando("revision-cerrar", "cerrar_revision", ("ejemplar_id", int))
    p.add_argument("--apto", type=int, choices=(0, 1), required=True)
    comando("reporte", "reporte", ("nombre", str))
    return parser


def main():
    parser = construir_parser()
    args = parser.parse_args()
    b = Biblioteca(args.db)
    try:
        datos = vars(args).copy()
        if args.comando == "revision-cerrar":
            datos["apto"] = bool(args.apto)
        resultado = ejecutar(b, datos)
        print(json.dumps({"resultado": "ok" if resultado is None else resultado},
                         ensure_ascii=False, indent=2))
    except ReglaNegocio as exc:
        parser.exit(2, f"Error de negocio: {exc}\n")


if __name__ == "__main__":
    main()
