"""Interfaz de consola: python -m biblioteca --help."""

import argparse
import json

from .aplicacion.biblioteca import Biblioteca
from .dominio.regla_negocio import ReglaNegocio
from .config import BASE_PREDETERMINADA


def construir_parser():
    parser = argparse.ArgumentParser(description="Red de bibliotecas: préstamos interbibliotecarios")
    parser.add_argument("--db", default=BASE_PREDETERMINADA, help="Archivo SQLite (por defecto biblioteca.db en la raíz del proyecto)")
    sub = parser.add_subparsers(dest="comando", required=True)

    def comando(nombre, *campos):
        p = sub.add_parser(nombre)
        for campo, tipo in campos:
            p.add_argument(campo, type=tipo)
        return p

    comando("sede-crear", ("nombre", str), ("direccion", str), ("contacto", str), ("horarios", str))
    p = comando("sede-editar", ("id", int))
    for campo in ("direccion", "contacto", "horarios"):
        p.add_argument(f"--{campo}")
    p.add_argument("--activa", type=int, choices=(0, 1))
    comando("socio-crear", ("documento", str), ("nombre", str), ("email", str))
    p = comando("socio-editar", ("id", int))
    p.add_argument("--nombre")
    p.add_argument("--email")
    p.add_argument("--habilitado", type=int, choices=(0, 1))
    p = comando("libro-crear", ("isbn", str), ("titulo", str), ("autor", str))
    p.add_argument("--anio", type=int)
    p = comando("libro-editar", ("id", int))
    p.add_argument("--titulo")
    p.add_argument("--autor")
    p.add_argument("--anio", type=int)
    comando("ejemplar-crear", ("codigo", str), ("libro_id", int), ("sede_id", int))
    comando("listar", ("tabla", str))
    p = comando("disponibilidad")
    p.add_argument("--sede", type=int)
    comando("reserva-crear", ("socio_id", int), ("libro_id", int), ("sede_id", int))
    comando("reserva-cancelar", ("id", int))
    comando("prestamo-solicitar", ("socio_id", int), ("ejemplar_id", int),
            ("origen_id", int), ("destino_id", int))
    comando("prestamo-entregar", ("id", int))
    p = comando("prestamo-devolver", ("id", int))
    p.add_argument("--condicion", choices=("BUENO", "DANADO", "DESTRUIDO", "EXTRAVIADO"), default="BUENO")
    p = comando("remito-avanzar", ("id", int), ("estado", str))
    p.add_argument("--detalle", default="")
    comando("remito-historial", ("id", int))
    p = comando("revision-cerrar", ("ejemplar_id", int))
    p.add_argument("--apto", type=int, choices=(0, 1), required=True)
    comando("reporte", ("nombre", str))
    return parser


def main():
    parser = construir_parser()
    args = parser.parse_args()
    b = Biblioteca(args.db)
    try:
        acciones = {
            "sede-crear": lambda: b.crear_sede(args.nombre, args.direccion, args.contacto, args.horarios),
            "sede-editar": lambda: b.actualizar_sede(args.id, direccion=args.direccion,
                contacto=args.contacto, horarios=args.horarios, activa=args.activa),
            "socio-crear": lambda: b.crear_socio(args.documento, args.nombre, args.email),
            "socio-editar": lambda: b.actualizar_socio(args.id, nombre=args.nombre,
                email=args.email, habilitado=args.habilitado),
            "libro-crear": lambda: b.crear_libro(args.isbn, args.titulo, args.autor, args.anio),
            "libro-editar": lambda: b.actualizar_libro(args.id, titulo=args.titulo,
                autor=args.autor, anio=args.anio),
            "ejemplar-crear": lambda: b.crear_ejemplar(args.codigo, args.libro_id, args.sede_id),
            "listar": lambda: b.listar(args.tabla),
            "disponibilidad": lambda: b.disponibilidad(args.sede),
            "reserva-crear": lambda: b.reservar(args.socio_id, args.libro_id, args.sede_id),
            "reserva-cancelar": lambda: b.cancelar_reserva(args.id),
            "prestamo-solicitar": lambda: b.solicitar_prestamo(args.socio_id, args.ejemplar_id,
                args.origen_id, args.destino_id),
            "prestamo-entregar": lambda: {"vence_en": b.entregar_prestamo(args.id)},
            "prestamo-devolver": lambda: {"multa_centavos": b.devolver_prestamo(args.id, args.condicion)},
            "remito-avanzar": lambda: b.avanzar_remito(args.id, args.estado.upper(), detalle=args.detalle),
            "remito-historial": lambda: b.historial_remito(args.id),
            "revision-cerrar": lambda: b.cerrar_revision(args.ejemplar_id, bool(args.apto)),
            "reporte": lambda: b.reportes(args.nombre),
        }
        resultado = acciones[args.comando]()
        print(json.dumps({"resultado": "ok" if resultado is None else resultado},
                         ensure_ascii=False, indent=2))
    except ReglaNegocio as exc:
        parser.exit(2, f"Error de negocio: {exc}\n")


if __name__ == "__main__":
    main()
