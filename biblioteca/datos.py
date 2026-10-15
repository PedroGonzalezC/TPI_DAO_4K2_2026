"""Persistencia SQLite, restricciones de integridad e historial de remitos."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


ESQUEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sedes (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, direccion TEXT NOT NULL,
 contacto TEXT NOT NULL, horarios TEXT NOT NULL, activa INTEGER NOT NULL DEFAULT 1 CHECK(activa IN (0,1))
);
CREATE TABLE IF NOT EXISTS socios (
 id INTEGER PRIMARY KEY, documento TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL,
 email TEXT NOT NULL, habilitado INTEGER NOT NULL DEFAULT 1 CHECK(habilitado IN (0,1))
);
CREATE TABLE IF NOT EXISTS libros (
 id INTEGER PRIMARY KEY, isbn TEXT NOT NULL UNIQUE, titulo TEXT NOT NULL,
 autor TEXT NOT NULL, anio INTEGER CHECK(anio IS NULL OR anio > 0)
);
CREATE TABLE IF NOT EXISTS ejemplares (
 id INTEGER PRIMARY KEY, codigo TEXT NOT NULL UNIQUE, libro_id INTEGER NOT NULL REFERENCES libros(id),
 sede_pertenencia_id INTEGER NOT NULL REFERENCES sedes(id), sede_actual_id INTEGER NOT NULL REFERENCES sedes(id),
 estado TEXT NOT NULL DEFAULT 'DISPONIBLE' CHECK(estado IN
 ('DISPONIBLE','APARTADO','RESERVADO','PRESTADO','EN_TRANSITO','POR_RETORNAR','EN_REVISION','BAJA'))
);
CREATE TABLE IF NOT EXISTS reservas (
 id INTEGER PRIMARY KEY, socio_id INTEGER NOT NULL REFERENCES socios(id),
 libro_id INTEGER NOT NULL REFERENCES libros(id), sede_id INTEGER NOT NULL REFERENCES sedes(id),
 ejemplar_id INTEGER REFERENCES ejemplares(id),
 estado TEXT NOT NULL DEFAULT 'EN_ESPERA' CHECK(estado IN ('EN_ESPERA','ASIGNADA','CUMPLIDA','CANCELADA')),
 creada_en TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS reserva_socio_activa ON reservas(socio_id, libro_id, sede_id)
 WHERE estado IN ('EN_ESPERA','ASIGNADA');
CREATE UNIQUE INDEX IF NOT EXISTS reserva_ejemplar_activa ON reservas(ejemplar_id)
 WHERE estado = 'ASIGNADA';
CREATE TABLE IF NOT EXISTS prestamos (
 id INTEGER PRIMARY KEY, socio_id INTEGER NOT NULL REFERENCES socios(id),
 ejemplar_id INTEGER NOT NULL REFERENCES ejemplares(id),
 sede_origen_id INTEGER NOT NULL REFERENCES sedes(id),
 sede_destino_id INTEGER NOT NULL REFERENCES sedes(id),
 tipo TEXT NOT NULL CHECK(tipo IN ('LOCAL','INTERBIBLIOTECARIO')),
 estado TEXT NOT NULL CHECK(estado IN ('SOLICITADO','EN_TRANSITO','LISTO','ACTIVO','DEVUELTO','CANCELADO')),
 solicitado_en TEXT NOT NULL, entregado_en TEXT, vence_en TEXT, devuelto_en TEXT,
 condicion_devolucion TEXT CHECK(condicion_devolucion IN ('BUENO','DANADO','DESTRUIDO','EXTRAVIADO')),
 multa_centavos INTEGER NOT NULL DEFAULT 0 CHECK(multa_centavos >= 0)
);
CREATE UNIQUE INDEX IF NOT EXISTS prestamo_vigente_ejemplar ON prestamos(ejemplar_id)
 WHERE estado NOT IN ('DEVUELTO','CANCELADO');
CREATE TABLE IF NOT EXISTS remitos (
 id INTEGER PRIMARY KEY, prestamo_id INTEGER NOT NULL REFERENCES prestamos(id),
 ejemplar_id INTEGER NOT NULL REFERENCES ejemplares(id),
 tipo TEXT NOT NULL CHECK(tipo IN ('IDA','REGRESO')),
 origen_id INTEGER NOT NULL REFERENCES sedes(id), destino_id INTEGER NOT NULL REFERENCES sedes(id),
 estado TEXT NOT NULL CHECK(estado IN ('CREADO','EMPAQUETADO','DESPACHADO','RECIBIDO')),
 creado_en TEXT NOT NULL, recibido_en TEXT,
 UNIQUE(prestamo_id, tipo), CHECK(origen_id <> destino_id)
);
CREATE TABLE IF NOT EXISTS historial_remitos (
 id INTEGER PRIMARY KEY, remito_id INTEGER NOT NULL REFERENCES remitos(id),
 estado TEXT NOT NULL, fecha TEXT NOT NULL, detalle TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_prestamos_estado ON prestamos(estado, vence_en);
CREATE INDEX IF NOT EXISTS idx_reservas_espera ON reservas(libro_id, sede_id, estado, creada_en);
"""


class HistorialRemito:
    """Observer persistente: registra cada evento en la misma transacción."""

    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def actualizar(self, remito_id: int, estado: str, fecha: str, detalle: str) -> None:
        self.conexion.execute(
            "INSERT INTO historial_remitos(remito_id,estado,fecha,detalle) VALUES(?,?,?,?)",
            (remito_id, estado, fecha, detalle),
        )


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
