"""Persistencia y reconstrucción de ejemplares físicos."""

import sqlite3

from ..dominio.catalogo.ejemplar import Ejemplar
from ..dominio.regla_negocio import ReglaNegocio


class EjemplarDAO:
    @staticmethod
    def desde_fila(fila: sqlite3.Row) -> Ejemplar:
        return Ejemplar(fila["id"], fila["codigo"], fila["libro_id"], fila["sede_pertenencia_id"],
                         fila["sede_actual_id"], fila["estado"])

    @classmethod
    def obtener(cls, con, ejemplar_id: int) -> Ejemplar:
        fila = con.execute("SELECT * FROM ejemplares WHERE id=?", (ejemplar_id,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe ejemplar con id {ejemplar_id}")
        return cls.desde_fila(fila)

    @staticmethod
    def crear(con, ejemplar: Ejemplar) -> int:
        return con.execute("""
            INSERT INTO ejemplares(codigo,libro_id,sede_pertenencia_id,sede_actual_id,estado)
            VALUES(?,?,?,?,?)
        """, (ejemplar.codigo, ejemplar.libro_id, ejemplar.sede_pertenencia_id,
              ejemplar.sede_actual_id, ejemplar.estado)).lastrowid

    @staticmethod
    def guardar(con, ejemplar: Ejemplar) -> None:
        con.execute("UPDATE ejemplares SET sede_actual_id=?,estado=? WHERE id=?",
                    (ejemplar.sede_actual_id, ejemplar.estado, ejemplar.id))

    @staticmethod
    def primero_disponible(con, libro_id: int, sede_id: int):
        fila = con.execute("""
            SELECT * FROM ejemplares WHERE libro_id=? AND sede_actual_id=?
            AND estado='DISPONIBLE' ORDER BY id LIMIT 1
        """, (libro_id, sede_id)).fetchone()
        return None if fila is None else EjemplarDAO.desde_fila(fila)
