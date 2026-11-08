"""Administrador de conexiones y transacciones SQLite."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .esquema import ESQUEMA


class BaseDatos:
    """Administrador de conexiones y transacciones sobre SQLite."""

    def __init__(self, ruta: str | Path) -> None:
        self.ruta = str(ruta)
        with self.conexion() as con:
            con.executescript(ESQUEMA)
            cols_ejemplares = {
                fila["name"] for fila in con.execute("PRAGMA table_info(ejemplares)")
            }
            if "condicion" not in cols_ejemplares:
                con.execute(
                    "ALTER TABLE ejemplares ADD COLUMN condicion TEXT NOT NULL DEFAULT 'BUENO' "
                    "CHECK(condicion IN ('BUENO','DANADO','DESTRUIDO','EXTRAVIADO'))"
                )
                con.execute(
                    """
                    UPDATE ejemplares
                    SET condicion = COALESCE(
                        (SELECT p.condicion_devolucion
                         FROM prestamos p
                         WHERE p.ejemplar_id = ejemplares.id
                           AND p.condicion_devolucion IS NOT NULL
                         ORDER BY p.devuelto_en DESC, p.id DESC
                         LIMIT 1),
                        condicion
                    )
                    """
                )
            cols_prestamos = {
                fila["name"] for fila in con.execute("PRAGMA table_info(prestamos)")
            }
            if "plazo_dias" not in cols_prestamos:
                con.execute(
                    "ALTER TABLE prestamos ADD COLUMN plazo_dias INTEGER NOT NULL DEFAULT 14 "
                    "CHECK(plazo_dias > 0)"
                )
            con.execute(
                """
                INSERT OR IGNORE INTO multas(
                    prestamo_id, socio_id, monto_centavos, dias_atraso, estado, creada_en
                )
                SELECT p.id, p.socio_id, p.multa_centavos,
                       MAX(1, CAST(p.multa_centavos / 10000 AS INTEGER)),
                       'PENDIENTE', COALESCE(p.devuelto_en, p.solicitado_en)
                FROM prestamos p
                WHERE p.multa_centavos > 0
                """
            )
            con.execute(
                """
                UPDATE socios
                SET habilitado = 0
                WHERE id IN (SELECT socio_id FROM multas WHERE estado = 'PENDIENTE')
                """
            )

    @contextmanager
    def conexion(self):
        con = sqlite3.connect(self.ruta)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
