"""DAO de Socio: acceso a datos de la tabla socios."""

import sqlite3

from ..models.socio import Socio


class SocioDAO:
    """Encapsula las consultas y operaciones SQL sobre socios."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    def crear(self, socio: Socio) -> int:
        cursor = self.con.execute(
            "INSERT INTO socios(documento, nombre, email, habilitado) VALUES(?, ?, ?, ?)",
            (socio.documento, socio.nombre, socio.email, int(socio.habilitado)),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, socio_id: int) -> Socio | None:
        fila = self.con.execute("SELECT * FROM socios WHERE id=?", (socio_id,)).fetchone()
        if fila is None:
            return None
        return Socio(
            id=fila["id"],
            documento=fila["documento"],
            nombre=fila["nombre"],
            email=fila["email"],
            habilitado=bool(fila["habilitado"]),
        )

    def listar(self) -> list[dict]:
        return [dict(fila) for fila in self.con.execute("SELECT * FROM socios ORDER BY id")]

    def actualizar(self, socio: Socio) -> None:
        self.con.execute(
            "UPDATE socios SET nombre=?, email=?, habilitado=? WHERE id=?",
            (socio.nombre, socio.email, int(socio.habilitado), socio.id),
        )
