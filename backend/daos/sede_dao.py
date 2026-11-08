"""DAO de Sede: acceso a datos de la tabla sedes."""

import sqlite3

from ..models.sede import Sede


class SedeDAO:
    """Encapsula las consultas y operaciones SQL sobre sedes."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    def crear(self, sede: Sede) -> int:
        cursor = self.con.execute(
            "INSERT INTO sedes(nombre, direccion, contacto, horarios, activa) VALUES(?, ?, ?, ?, ?)",
            (sede.nombre, sede.direccion, sede.contacto, sede.horarios, int(sede.activa)),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, sede_id: int) -> Sede | None:
        fila = self.con.execute("SELECT * FROM sedes WHERE id=?", (sede_id,)).fetchone()
        if fila is None:
            return None
        return Sede(
            id=fila["id"],
            nombre=fila["nombre"],
            direccion=fila["direccion"],
            contacto=fila["contacto"],
            horarios=fila["horarios"],
            activa=bool(fila["activa"]),
        )

    def listar(self) -> list[dict]:
        return [dict(fila) for fila in self.con.execute("SELECT * FROM sedes ORDER BY id")]

    def actualizar(self, sede: Sede) -> None:
        self.con.execute(
            "UPDATE sedes SET direccion=?, contacto=?, horarios=?, activa=? WHERE id=?",
            (sede.direccion, sede.contacto, sede.horarios, int(sede.activa), sede.id),
        )
