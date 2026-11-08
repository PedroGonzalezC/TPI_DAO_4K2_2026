"""DAO de Prestamo: acceso a datos de préstamos y consultas de reportes asociados."""

import sqlite3

from ..models.fabrica_prestamos import FabricaPrestamos
from ..models.prestamo import Prestamo


class PrestamoDAO:
    """Encapsula las consultas y operaciones SQL sobre préstamos."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.con = conexion

    def obtener_por_id(self, prestamo_id: int) -> Prestamo | None:
        fila = self.con.execute("SELECT * FROM prestamos WHERE id=?", (prestamo_id,)).fetchone()
        if fila is None:
            return None
        return FabricaPrestamos.reconstruir(**dict(fila))

    def listar(self) -> list[dict]:
        return [dict(fila) for fila in self.con.execute("SELECT * FROM prestamos ORDER BY id")]

    def actualizar(self, prestamo: Prestamo) -> None:
        self.con.execute(
            """
            UPDATE prestamos
            SET estado=?, entregado_en=?, vence_en=?, devuelto_en=?,
                condicion_devolucion=?, multa_centavos=?
            WHERE id=?
            """,
            (
                prestamo.estado,
                prestamo.entregado_en,
                prestamo.vence_en,
                prestamo.devuelto_en,
                prestamo.condicion_devolucion,
                prestamo.multa_centavos,
                prestamo.id,
            ),
        )

    def reporte_activos_transito(self) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT p.id, l.titulo, e.codigo, so.nombre socio, p.tipo,
                       CASE WHEN r.id IS NOT NULL THEN 'RETORNO_EN_TRANSITO' ELSE p.estado END estado,
                       CASE WHEN r.id IS NOT NULL THEN d.nombre ELSE o.nombre END origen,
                       CASE WHEN r.id IS NOT NULL THEN o.nombre ELSE d.nombre END destino,
                       p.vence_en
                FROM prestamos p JOIN ejemplares e ON e.id=p.ejemplar_id
                JOIN libros l ON l.id=e.libro_id JOIN socios so ON so.id=p.socio_id
                JOIN sedes o ON o.id=p.sede_origen_id JOIN sedes d ON d.id=p.sede_destino_id
                LEFT JOIN remitos r ON r.prestamo_id=p.id AND r.tipo='REGRESO' AND r.estado='DESPACHADO'
                WHERE p.estado IN ('ACTIVO','EN_TRANSITO','LISTO') OR r.id IS NOT NULL
                ORDER BY p.id
                """
            )
        ]

    def reporte_vencidos_multas(self, hoy_iso: str, multa_diaria_centavos: int) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT p.id, so.nombre socio, l.titulo, p.vence_en,
                       CAST(julianday(?) - julianday(p.vence_en) AS INTEGER) dias_atraso,
                       CAST(julianday(?) - julianday(p.vence_en) AS INTEGER) * ? multa_estimada_centavos
                FROM prestamos p JOIN socios so ON so.id=p.socio_id
                JOIN ejemplares e ON e.id=p.ejemplar_id JOIN libros l ON l.id=e.libro_id
                WHERE p.estado='ACTIVO' AND p.vence_en < ?
                ORDER BY dias_atraso DESC
                """,
                (hoy_iso, hoy_iso, multa_diaria_centavos, hoy_iso),
            )
        ]

    def reporte_mas_solicitados(self) -> list[dict]:
        return [
            dict(fila)
            for fila in self.con.execute(
                """
                SELECT l.id, l.titulo, l.isbn, COUNT(*) solicitudes_interbibliotecarias
                FROM prestamos p JOIN ejemplares e ON e.id=p.ejemplar_id
                JOIN libros l ON l.id=e.libro_id
                WHERE p.tipo='INTERBIBLIOTECARIO'
                GROUP BY l.id ORDER BY solicitudes_interbibliotecarias DESC, l.titulo
                """
            )
        ]
