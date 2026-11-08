"""DAO de Ejemplar: acceso a datos de copias físicas y consultas de disponibilidad."""

import sqlite3

from ..models.ejemplar import Ejemplar


class EjemplarDAO:
    """Encapsula las consultas y operaciones SQL sobre ejemplares."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    @staticmethod
    def _mapear(fila: sqlite3.Row) -> Ejemplar:
        return Ejemplar(
            id=fila["id"],
            codigo=fila["codigo"],
            libro_id=fila["libro_id"],
            sede_pertenencia_id=fila["sede_pertenencia_id"],
            sede_actual_id=fila["sede_actual_id"],
            estado=fila["estado"],
            condicion=fila["condicion"] if "condicion" in fila.keys() else "BUENO",
        )

    def crear(self, ejemplar: Ejemplar) -> int:
        cursor = self.con.execute(
            """
            INSERT INTO ejemplares(codigo, libro_id, sede_pertenencia_id, sede_actual_id, estado, condicion)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                ejemplar.codigo,
                ejemplar.libro_id,
                ejemplar.sede_pertenencia_id,
                ejemplar.sede_actual_id,
                ejemplar.estado,
                ejemplar.condicion,
            ),
        )
        return int(cursor.lastrowid)

    def obtener_por_id(self, ejemplar_id: int) -> Ejemplar | None:
        fila = self.con.execute("SELECT * FROM ejemplares WHERE id=?", (ejemplar_id,)).fetchone()
        return self._mapear(fila) if fila is not None else None

    def buscar_disponible_en_sede(self, libro_id: int, sede_id: int) -> Ejemplar | None:
        fila = self.con.execute(
            """
            SELECT * FROM ejemplares
            WHERE libro_id=? AND sede_actual_id=? AND estado='DISPONIBLE'
            ORDER BY id LIMIT 1
            """,
            (libro_id, sede_id),
        ).fetchone()
        return self._mapear(fila) if fila is not None else None

    def listar(self) -> list[dict]:
        return [dict(fila) for fila in self.con.execute("SELECT * FROM ejemplares ORDER BY id")]

    def actualizar(self, ejemplar: Ejemplar) -> None:
        self.con.execute(
            "UPDATE ejemplares SET sede_actual_id=?, estado=?, condicion=? WHERE id=?",
            (ejemplar.sede_actual_id, ejemplar.estado, ejemplar.condicion, ejemplar.id),
        )

    def consultar_disponibilidad(self, sede_id: int | None = None) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT s.id sede_id, s.nombre sede, l.id libro_id, l.isbn, l.titulo,
                       COUNT(e.id) ejemplares_totales,
                       SUM(CASE WHEN e.estado='DISPONIBLE' THEN 1 ELSE 0 END) disponibles
                FROM sedes s JOIN ejemplares e ON e.sede_actual_id=s.id
                JOIN libros l ON l.id=e.libro_id
                WHERE (? IS NULL OR s.id=?)
                GROUP BY s.id, l.id ORDER BY s.nombre, l.titulo
                """,
                (sede_id, sede_id),
            )
        ]

    def reporte_disponibilidad(self) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT s.nombre sede, l.titulo, COUNT(e.id) total,
                       SUM(CASE WHEN e.estado='DISPONIBLE' THEN 1 ELSE 0 END) disponibles,
                       SUM(CASE WHEN e.estado='EN_TRANSITO' THEN 1 ELSE 0 END) en_transito
                FROM ejemplares e JOIN sedes s ON s.id=e.sede_actual_id
                JOIN libros l ON l.id=e.libro_id
                GROUP BY s.id, l.id ORDER BY s.nombre, l.titulo
                """
            )
        ]
