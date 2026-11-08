"""DAO de Multa: acceso a datos de la tabla multas y deuda por socio."""

import sqlite3

from ..models.multa import Multa


class MultaDAO:
    """Encapsula las consultas y operaciones SQL sobre multas."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    @staticmethod
    def _mapear(fila: sqlite3.Row) -> Multa:
        return Multa(
            id=fila["id"],
            prestamo_id=fila["prestamo_id"],
            socio_id=fila["socio_id"],
            monto_centavos=fila["monto_centavos"],
            dias_atraso=fila["dias_atraso"],
            estado=fila["estado"],
            creada_en=fila["creada_en"],
            pagada_en=fila["pagada_en"],
        )

    def crear(self, multa: Multa) -> int:
        cursor = self.con.execute(
            """
            INSERT INTO multas(
                prestamo_id, socio_id, monto_centavos, dias_atraso, estado, creada_en, pagada_en
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                multa.prestamo_id,
                multa.socio_id,
                multa.monto_centavos,
                multa.dias_atraso,
                multa.estado,
                multa.creada_en,
                multa.pagada_en,
            ),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, multa_id: int) -> Multa | None:
        fila = self.con.execute("SELECT * FROM multas WHERE id=?", (multa_id,)).fetchone()
        return self._mapear(fila) if fila is not None else None

    def obtener_por_prestamo(self, prestamo_id: int) -> Multa | None:
        fila = self.con.execute(
            "SELECT * FROM multas WHERE prestamo_id=?", (prestamo_id,)
        ).fetchone()
        return self._mapear(fila) if fila is not None else None

    def actualizar(self, multa: Multa) -> None:
        self.con.execute(
            "UPDATE multas SET estado=?, pagada_en=? WHERE id=?",
            (multa.estado, multa.pagada_en, multa.id),
        )

    def tiene_pendientes_por_socio(self, socio_id: int) -> bool:
        fila = self.con.execute(
            "SELECT 1 FROM multas WHERE socio_id=? AND estado='PENDIENTE' LIMIT 1",
            (socio_id,),
        ).fetchone()
        return fila is not None

    def listar(self) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT m.*, s.nombre socio_nombre, s.documento socio_documento,
                       p.ejemplar_id, e.codigo ejemplar_codigo, l.titulo libro_titulo
                FROM multas m
                JOIN socios s ON s.id = m.socio_id
                JOIN prestamos p ON p.id = m.prestamo_id
                JOIN ejemplares e ON e.id = p.ejemplar_id
                JOIN libros l ON l.id = e.libro_id
                ORDER BY CASE WHEN m.estado='PENDIENTE' THEN 0 ELSE 1 END, m.id DESC
                """
            )
        ]
