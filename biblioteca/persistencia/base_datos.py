"""Conexiones y transacciones SQLite de la biblioteca."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .esquema import ESQUEMA


class BaseDatos:
    def __init__(self, ruta: str | Path):
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
