"""DAO de Remito: acceso a datos de la tabla remitos y reportes logísticos."""

import sqlite3

from ..models.remito import Remito


class RemitoDAO:
    """Encapsula las consultas y operaciones SQL sobre remitos."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    @staticmethod
    def _mapear(fila: sqlite3.Row) -> Remito:
        return Remito(
            id=fila["id"],
            estado=fila["estado"],
            prestamo_id=fila["prestamo_id"],
            ejemplar_id=fila["ejemplar_id"],
            tipo=fila["tipo"],
            origen_id=fila["origen_id"],
            destino_id=fila["destino_id"],
            creado_en=fila["creado_en"],
            recibido_en=fila["recibido_en"],
        )

    def crear(self, remito: Remito) -> int:
        cursor = self.con.execute(
            """
            INSERT INTO remitos(prestamo_id, ejemplar_id, tipo, origen_id, destino_id, estado, creado_en)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                remito.prestamo_id,
                remito.ejemplar_id,
                remito.tipo,
                remito.origen_id,
                remito.destino_id,
                remito.estado,
                remito.creado_en,
            ),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, remito_id: int) -> Remito | None:
        fila = self.con.execute("SELECT * FROM remitos WHERE id=?", (remito_id,)).fetchone()
        return self._mapear(fila) if fila is not None else None

    def obtener_por_prestamo_y_tipo(self, prestamo_id: int, tipo: str) -> Remito | None:
        fila = self.con.execute(
            "SELECT * FROM remitos WHERE prestamo_id=? AND tipo=?",
            (prestamo_id, tipo),
        ).fetchone()
        return self._mapear(fila) if fila is not None else None

    def listar(self) -> list[dict]:
        return [dict(fila) for fila in self.con.execute("SELECT * FROM remitos ORDER BY id")]

    def actualizar(self, remito: Remito) -> None:
        self.con.execute(
            "UPDATE remitos SET estado=?, recibido_en=? WHERE id=?",
            (remito.estado, remito.recibido_en, remito.id),
        )

    def reporte_logistica(self) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT COUNT(*) envios,
                       SUM(CASE WHEN estado='RECIBIDO' THEN 1 ELSE 0 END) recibidos,
                       SUM(CASE WHEN estado='DESPACHADO' THEN 1 ELSE 0 END) en_transito,
                       ROUND(100.0 * SUM(CASE WHEN estado='RECIBIDO' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) tasa_recepcion_pct,
                       ROUND(AVG(CASE WHEN estado='RECIBIDO' THEN
                         (julianday(recibido_en)-julianday(creado_en))*24 END), 2) horas_promedio_trayecto
                FROM remitos
                """
            )
        ]

    def reporte_movimientos(self) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT o.nombre origen, d.nombre destino, r.tipo, COUNT(*) envios,
                       ROUND(AVG(CASE WHEN r.estado='RECIBIDO' THEN
                         (julianday(r.recibido_en)-julianday(creado_en))*24 END), 2) horas_promedio
                FROM remitos r JOIN sedes o ON o.id=r.origen_id JOIN sedes d ON d.id=r.destino_id
                GROUP BY r.origen_id, r.destino_id, r.tipo ORDER BY envios DESC
                """
            )
        ]
