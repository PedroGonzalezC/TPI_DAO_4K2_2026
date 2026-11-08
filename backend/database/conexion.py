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
