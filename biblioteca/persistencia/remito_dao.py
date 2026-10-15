"""Persistencia y reconstrucción de remitos."""

from ..dominio.regla_negocio import ReglaNegocio
from ..dominio.remitos.remito import Remito


class RemitoDAO:
    @classmethod
    def obtener(cls, con, remito_id: int):
        fila = con.execute("SELECT * FROM remitos WHERE id=?", (remito_id,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe remito con id {remito_id}")
        return Remito(fila["id"], fila["estado"]), fila

    @staticmethod
    def crear(con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha) -> int:
        return con.execute("""
            INSERT INTO remitos(prestamo_id,ejemplar_id,tipo,origen_id,destino_id,estado,creado_en)
            VALUES(?,?,?,?,?,'CREADO',?)
        """, (prestamo_id, ejemplar_id, tipo, origen, destino, fecha)).lastrowid

    @staticmethod
    def guardar(con, remito: Remito, recibido_en: str | None) -> None:
        con.execute("UPDATE remitos SET estado=?,recibido_en=? WHERE id=?",
                    (remito.estado, recibido_en, remito.id))

    @staticmethod
    def ultima_fecha(con, remito_id: int) -> str:
        return con.execute("SELECT fecha FROM historial_remitos WHERE remito_id=? ORDER BY id DESC LIMIT 1",
                           (remito_id,)).fetchone()["fecha"]

    @staticmethod
    def fecha_recepcion_ida(con, prestamo_id: int) -> str:
        return con.execute("SELECT recibido_en FROM remitos WHERE prestamo_id=? AND tipo='IDA'",
                           (prestamo_id,)).fetchone()["recibido_en"]

    @staticmethod
    def historial(con, remito_id: int):
        return [dict(x) for x in con.execute(
            "SELECT estado,fecha,detalle FROM historial_remitos WHERE remito_id=? ORDER BY id", (remito_id,)
        )]
