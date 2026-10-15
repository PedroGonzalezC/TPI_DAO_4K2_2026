"""Persistencia y reconstrucción de socios."""

import sqlite3

from ..dominio.personas.socio import Socio
from ..dominio.regla_negocio import ReglaNegocio


class SocioDAO:
    @staticmethod
    def desde_fila(fila: sqlite3.Row) -> Socio:
        return Socio(fila["id"], fila["documento"], fila["nombre"], fila["email"], bool(fila["habilitado"]))

    @classmethod
    def obtener(cls, con, socio_id: int) -> Socio:
        fila = con.execute("SELECT * FROM socios WHERE id=?", (socio_id,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe socio con id {socio_id}")
        return cls.desde_fila(fila)

    @staticmethod
    def crear(con, socio: Socio) -> int:
        return con.execute("INSERT INTO socios(documento,nombre,email,habilitado) VALUES(?,?,?,?)",
                           (socio.documento, socio.nombre, socio.email, int(socio.habilitado))).lastrowid

    @staticmethod
    def guardar(con, socio: Socio) -> None:
        con.execute("UPDATE socios SET nombre=?,email=?,habilitado=? WHERE id=?",
                    (socio.nombre, socio.email, int(socio.habilitado), socio.id))
