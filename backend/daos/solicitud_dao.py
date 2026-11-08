"""DAO de Solicitud: acceso a datos de solicitudes de préstamo."""

import sqlite3

from ..models.fabrica_prestamos import FabricaPrestamos
from ..models.prestamo import Prestamo


class SolicitudDAO:
    """Encapsula el alta y consulta de solicitudes de préstamo."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    def crear(self, solicitud: Prestamo) -> int:
        cursor = self.con.execute(
            """
            INSERT INTO prestamos(
                socio_id, ejemplar_id, sede_origen_id, sede_destino_id,
                tipo, estado, plazo_dias, solicitado_en
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                solicitud.socio_id,
                solicitud.ejemplar_id,
                solicitud.sede_origen_id,
                solicitud.sede_destino_id,
                solicitud.tipo,
                solicitud.estado,
                solicitud.plazo_dias,
                solicitud.solicitado_en,
            ),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, solicitud_id: int) -> Prestamo | None:
        fila = self.con.execute("SELECT * FROM prestamos WHERE id=?", (solicitud_id,)).fetchone()
        if fila is None:
            return None
        return FabricaPrestamos.reconstruir(**dict(fila))

    def listar_pendientes(self) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                "SELECT * FROM prestamos WHERE estado IN ('SOLICITADO', 'EN_TRANSITO', 'LISTO') ORDER BY id"
            )
        ]
