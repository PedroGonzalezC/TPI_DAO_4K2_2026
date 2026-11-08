"""DAO de EventoRemito: acceso a datos de eventos del remito (historial_remitos) y observador persistente."""

import sqlite3

from ..models.evento_remito import EventoRemito


class EventoRemitoDAO:
    """Encapsula el registro y consulta de eventos del historial de un remito."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    def registrar(self, evento: EventoRemito) -> int:
        cursor = self.con.execute(
            "INSERT INTO historial_remitos(remito_id, estado, fecha, detalle) VALUES(?, ?, ?, ?)",
            (evento.remito_id, evento.estado, evento.fecha, evento.detalle),
        )
        return int(cursor.lastrowid)

    def actualizar(self, remito_id: int, estado: str, fecha: str, detalle: str) -> None:
        """Implementación de ObservadorRemito para persistir cada transición."""
        self.registrar(EventoRemito(remito_id=remito_id, estado=estado, fecha=fecha, detalle=detalle))

    def obtener_ultimo_por_remito(self, remito_id: int) -> EventoRemito | None:
        fila = self.con.execute(
            "SELECT * FROM historial_remitos WHERE remito_id=? ORDER BY id DESC LIMIT 1",
            (remito_id,),
        ).fetchone()
        if fila is None:
            return None
        return EventoRemito(
            id=fila["id"],
            remito_id=fila["remito_id"],
            estado=fila["estado"],
            fecha=fila["fecha"],
            detalle=fila["detalle"],
        )

    def listar_por_remito(self, remito_id: int) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                "SELECT estado, fecha, detalle FROM historial_remitos WHERE remito_id=? ORDER BY id",
                (remito_id,),
            )
        ]
