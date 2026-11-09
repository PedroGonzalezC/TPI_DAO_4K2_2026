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

    def tiene_prestamos_activos(self, socio_id: int) -> bool:
        fila = self.con.execute(
            "SELECT 1 FROM prestamos WHERE socio_id=? AND estado NOT IN ('DEVUELTO', 'CANCELADO') LIMIT 1",
            (socio_id,),
        ).fetchone()
        return fila is not None

    def tiene_historial(self, socio_id: int) -> bool:
        for tabla in ("prestamos", "reservas", "multas"):
            if self.con.execute(f"SELECT 1 FROM {tabla} WHERE socio_id=? LIMIT 1", (socio_id,)).fetchone() is not None:
                return True
        return False

    def eliminar(self, socio_id: int) -> None:
        self.con.execute("DELETE FROM socios WHERE id=?", (socio_id,))
