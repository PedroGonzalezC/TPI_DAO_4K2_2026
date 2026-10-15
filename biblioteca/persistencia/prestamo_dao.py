"""Persistencia y reconstrucción de préstamos."""

from ..dominio.prestamos.fabrica_prestamos import FabricaPrestamos
from ..dominio.regla_negocio import ReglaNegocio


class PrestamoDAO:
    @staticmethod
    def desde_fila(fila):
        return FabricaPrestamos.crear(fila["socio_id"], fila["ejemplar_id"], fila["sede_origen_id"],
                                      fila["sede_destino_id"], fila["estado"])

    @classmethod
    def obtener(cls, con, prestamo_id: int):
        fila = con.execute("SELECT * FROM prestamos WHERE id=?", (prestamo_id,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe prestamo con id {prestamo_id}")
        return cls.desde_fila(fila), fila

    @staticmethod
    def crear(con, prestamo, solicitado_en: str) -> int:
        return con.execute("""
            INSERT INTO prestamos(socio_id,ejemplar_id,sede_origen_id,sede_destino_id,tipo,estado,solicitado_en)
            VALUES(?,?,?,?,?,?,?)
        """, (prestamo.socio_id, prestamo.ejemplar_id, prestamo.sede_origen_id,
              prestamo.sede_destino_id, prestamo.tipo, prestamo.estado, solicitado_en)).lastrowid

    @staticmethod
    def guardar_estado(con, prestamo_id: int, prestamo) -> None:
        con.execute("UPDATE prestamos SET estado=? WHERE id=?", (prestamo.estado, prestamo_id))

    @staticmethod
    def activar(con, prestamo_id: int, prestamo, entregado_en: str, vence_en: str) -> None:
        con.execute("UPDATE prestamos SET estado=?,entregado_en=?,vence_en=? WHERE id=?",
                    (prestamo.estado, entregado_en, vence_en, prestamo_id))

    @staticmethod
    def devolver(con, prestamo_id: int, prestamo, devuelto_en: str, condicion: str, multa_centavos: int) -> None:
        con.execute("""
            UPDATE prestamos SET estado=?,devuelto_en=?,condicion_devolucion=?,multa_centavos=? WHERE id=?
        """, (prestamo.estado, devuelto_en, condicion, multa_centavos, prestamo_id))
