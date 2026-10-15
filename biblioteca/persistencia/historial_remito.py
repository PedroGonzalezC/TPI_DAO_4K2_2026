"""Observador que persiste cada cambio del remito."""

import sqlite3


class HistorialRemito:
    """Registra el evento dentro de la transacción del caso de uso."""

    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def actualizar(self, remito_id: int, estado: str, fecha: str, detalle: str) -> None:
        self.conexion.execute(
            "INSERT INTO historial_remitos(remito_id,estado,fecha,detalle) VALUES(?,?,?,?)",
            (remito_id, estado, fecha, detalle),
        )
