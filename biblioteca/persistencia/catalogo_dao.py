"""Acceso a datos maestros y consulta de disponibilidad."""

import sqlite3

from ..dominio.regla_negocio import ReglaNegocio


TABLAS = frozenset({"sedes", "socios", "libros", "ejemplares", "reservas", "prestamos", "remitos"})


class CatalogoDAO:
    @staticmethod
    def obtener(con: sqlite3.Connection, tabla: str, id_: int):
        if tabla not in TABLAS:
            raise ValueError("Tabla inválida")
        fila = con.execute(f"SELECT * FROM {tabla} WHERE id=?", (id_,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe {tabla[:-1]} con id {id_}")
        return fila

    @staticmethod
    def listar(con: sqlite3.Connection, tabla: str):
        if tabla not in TABLAS:
            raise ReglaNegocio("Listado desconocido")
        return [dict(x) for x in con.execute(f"SELECT * FROM {tabla} ORDER BY id")]

    @staticmethod
    def crear_sede(con, valores):
        return con.execute(
            "INSERT INTO sedes(nombre,direccion,contacto,horarios) VALUES(?,?,?,?)", valores
        ).lastrowid

    @staticmethod
    def actualizar_sede(con, sede_id, direccion, contacto, horarios, activa):
        con.execute(
            "UPDATE sedes SET direccion=?, contacto=?, horarios=?, activa=? WHERE id=?",
            (direccion, contacto, horarios, activa, sede_id),
        )

    @staticmethod
    def crear_socio(con, valores):
        return con.execute(
            "INSERT INTO socios(documento,nombre,email) VALUES(?,?,?)", valores
        ).lastrowid

    @staticmethod
    def actualizar_socio(con, socio_id, nombre, email, habilitado):
        con.execute(
            "UPDATE socios SET nombre=?, email=?, habilitado=? WHERE id=?",
            (nombre, email, habilitado, socio_id),
        )

    @staticmethod
    def crear_libro(con, valores):
        return con.execute(
            "INSERT INTO libros(isbn,titulo,autor,anio) VALUES(?,?,?,?)", valores
        ).lastrowid

    @staticmethod
    def actualizar_libro(con, libro_id, titulo, autor, anio):
        con.execute(
            "UPDATE libros SET titulo=?, autor=?, anio=? WHERE id=?",
            (titulo, autor, anio, libro_id),
        )

    @staticmethod
    def crear_ejemplar(con, codigo, libro_id, sede_id):
        return con.execute(
            "INSERT INTO ejemplares(codigo,libro_id,sede_pertenencia_id,sede_actual_id) VALUES(?,?,?,?)",
            (codigo, libro_id, sede_id, sede_id),
        ).lastrowid

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
