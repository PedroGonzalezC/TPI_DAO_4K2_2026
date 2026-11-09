"""DAO de Reserva: acceso a datos de la tabla reservas."""

import sqlite3

from ..models.reserva import Reserva


class ReservaDAO:
    """Encapsula las consultas y operaciones SQL sobre reservas."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    @staticmethod
    def _mapear(fila: sqlite3.Row) -> Reserva:
        return Reserva(
            id=fila["id"],
            socio_id=fila["socio_id"],
            libro_id=fila["libro_id"],
            sede_id=fila["sede_id"],
            ejemplar_id=fila["ejemplar_id"],
            estado=fila["estado"],
            creada_en=fila["creada_en"],
        )

    def crear(self, reserva: Reserva) -> int:
        cursor = self.con.execute(
            "INSERT INTO reservas(socio_id, libro_id, sede_id, estado, creada_en) VALUES(?, ?, ?, ?, ?)",
            (reserva.socio_id, reserva.libro_id, reserva.sede_id, reserva.estado, reserva.creada_en),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, reserva_id: int) -> Reserva | None:
        fila = self.con.execute("SELECT * FROM reservas WHERE id=?", (reserva_id,)).fetchone()
        return self._mapear(fila) if fila is not None else None

    def obtener_asignada_por_ejemplar(self, ejemplar_id: int) -> Reserva | None:
        fila = self.con.execute(
            "SELECT * FROM reservas WHERE ejemplar_id=? AND estado='ASIGNADA'",
            (ejemplar_id,),
        ).fetchone()
        return self._mapear(fila) if fila is not None else None

    def obtener_activa_por_socio_libro_sede(
        self, socio_id: int, libro_id: int, sede_id: int
    ) -> Reserva | None:
        fila = self.con.execute(
            """
            SELECT * FROM reservas
            WHERE socio_id=? AND libro_id=? AND sede_id=?
              AND estado IN ('EN_ESPERA', 'ASIGNADA')
            LIMIT 1
            """,
            (socio_id, libro_id, sede_id),
        ).fetchone()
        return self._mapear(fila) if fila is not None else None

    def buscar_primera_en_espera_habilitada(self, libro_id: int, sede_id: int) -> Reserva | None:
        fila = self.con.execute(
            """
            SELECT r.* FROM reservas r
            JOIN socios so ON so.id=r.socio_id
            JOIN sedes s ON s.id=r.sede_id
            WHERE r.libro_id=? AND r.sede_id=?
              AND r.estado='EN_ESPERA' AND so.habilitado=1 AND s.activa=1
            ORDER BY r.creada_en, r.id LIMIT 1
            """,
            (libro_id, sede_id),
        ).fetchone()
        return self._mapear(fila) if fila is not None else None

    def listar(self) -> list[dict]:
        return [dict(fila) for fila in self.con.execute("SELECT * FROM reservas ORDER BY id")]

    def actualizar(self, reserva: Reserva) -> None:
        self.con.execute(
            "UPDATE reservas SET estado=?, ejemplar_id=? WHERE id=?",
            (reserva.estado, reserva.ejemplar_id, reserva.id),
        )
