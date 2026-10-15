"""Persistencia y reconstrucción de sedes."""

import sqlite3

from ..dominio.personas.sede import Sede
from ..dominio.regla_negocio import ReglaNegocio


class SedeDAO:
    @staticmethod
    def desde_fila(fila: sqlite3.Row) -> Sede:
        return Sede(fila["id"], fila["nombre"], fila["direccion"], fila["contacto"],
                    fila["horarios"], bool(fila["activa"]))

    @classmethod
    def obtener(cls, con, sede_id: int) -> Sede:
        fila = con.execute("SELECT * FROM sedes WHERE id=?", (sede_id,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe sede con id {sede_id}")
        return cls.desde_fila(fila)

    @staticmethod
    def crear(con, sede: Sede) -> int:
        return con.execute("INSERT INTO sedes(nombre,direccion,contacto,horarios,activa) VALUES(?,?,?,?,?)",
                           (sede.nombre, sede.direccion, sede.contacto, sede.horarios, int(sede.activa))).lastrowid

    @staticmethod
    def guardar(con, sede: Sede) -> None:
        con.execute("UPDATE sedes SET direccion=?,contacto=?,horarios=?,activa=? WHERE id=?",
                    (sede.direccion, sede.contacto, sede.horarios, int(sede.activa), sede.id))
