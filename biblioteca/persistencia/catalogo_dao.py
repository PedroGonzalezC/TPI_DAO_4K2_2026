"""Acceso a datos maestros y consulta de disponibilidad."""

import sqlite3

from ..dominio.regla_negocio import ReglaNegocio


TABLAS = frozenset({"sedes", "socios", "libros", "ejemplares", "reservas", "prestamos", "remitos"})


class CatalogoDAO:
    @staticmethod
    def listar(con: sqlite3.Connection, tabla: str):
        if tabla not in TABLAS:
            raise ReglaNegocio("Listado desconocido")
        return [dict(x) for x in con.execute(f"SELECT * FROM {tabla} ORDER BY id")]

    @staticmethod
    def disponibilidad(con, sede_id):
        return [dict(x) for x in con.execute("""
            SELECT s.id sede_id, s.nombre sede, l.id libro_id, l.isbn, l.titulo,
                   COUNT(e.id) ejemplares_totales,
                   SUM(CASE WHEN e.estado='DISPONIBLE' THEN 1 ELSE 0 END) disponibles
            FROM sedes s JOIN ejemplares e ON e.sede_actual_id=s.id
            JOIN libros l ON l.id=e.libro_id
            WHERE (? IS NULL OR s.id=?)
            GROUP BY s.id,l.id ORDER BY s.nombre,l.titulo
        """, (sede_id, sede_id))]
