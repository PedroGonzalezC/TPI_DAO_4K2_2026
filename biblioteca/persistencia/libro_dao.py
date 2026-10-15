"""Persistencia y reconstrucción de libros."""

import sqlite3

from ..dominio.catalogo.libro import Libro
from ..dominio.regla_negocio import ReglaNegocio


class LibroDAO:
    @staticmethod
    def desde_fila(fila: sqlite3.Row) -> Libro:
        return Libro(fila["id"], fila["isbn"], fila["titulo"], fila["autor"], fila["anio"])

    @classmethod
    def obtener(cls, con, libro_id: int) -> Libro:
        fila = con.execute("SELECT * FROM libros WHERE id=?", (libro_id,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe libro con id {libro_id}")
        return cls.desde_fila(fila)

    @staticmethod
    def crear(con, libro: Libro) -> int:
        return con.execute("INSERT INTO libros(isbn,titulo,autor,anio) VALUES(?,?,?,?)",
                           (libro.isbn, libro.titulo, libro.autor, libro.anio)).lastrowid

    @staticmethod
    def guardar(con, libro: Libro) -> None:
        con.execute("UPDATE libros SET titulo=?,autor=?,anio=? WHERE id=?",
                    (libro.titulo, libro.autor, libro.anio, libro.id))
