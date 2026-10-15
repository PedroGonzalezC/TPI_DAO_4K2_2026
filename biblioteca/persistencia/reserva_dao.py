"""Persistencia de reservas y su cola de espera."""

from ..dominio.regla_negocio import ReglaNegocio
from ..dominio.reservas.reserva import Reserva


class ReservaDAO:
    @staticmethod
    def desde_fila(fila) -> Reserva:
        return Reserva(fila["id"], fila["socio_id"], fila["libro_id"], fila["sede_id"],
                       fila["creada_en"], fila["ejemplar_id"], fila["estado"])

    @classmethod
    def obtener(cls, con, reserva_id: int) -> Reserva:
        fila = con.execute("SELECT * FROM reservas WHERE id=?", (reserva_id,)).fetchone()
        if fila is None:
            raise ReglaNegocio(f"No existe reserva con id {reserva_id}")
        return cls.desde_fila(fila)

    @staticmethod
    def crear(con, reserva: Reserva) -> int:
        return con.execute("""
            INSERT INTO reservas(socio_id,libro_id,sede_id,ejemplar_id,estado,creada_en)
            VALUES(?,?,?,?,?,?)
        """, (reserva.socio_id, reserva.libro_id, reserva.sede_id, reserva.ejemplar_id,
              reserva.estado, reserva.creada_en)).lastrowid

    @staticmethod
    def guardar(con, reserva: Reserva) -> None:
        con.execute("UPDATE reservas SET ejemplar_id=?,estado=? WHERE id=?",
                    (reserva.ejemplar_id, reserva.estado, reserva.id))

    @staticmethod
    def primera_en_espera(con, libro_id: int, sede_id: int):
        fila = con.execute("""
            SELECT r.* FROM reservas r JOIN socios so ON so.id=r.socio_id
            JOIN sedes s ON s.id=r.sede_id WHERE r.libro_id=? AND r.sede_id=?
            AND r.estado='EN_ESPERA' AND so.habilitado=1 AND s.activa=1
            ORDER BY r.creada_en,r.id LIMIT 1
        """, (libro_id, sede_id)).fetchone()
        return None if fila is None else ReservaDAO.desde_fila(fila)

    @staticmethod
    def asignada_del_ejemplar(con, ejemplar_id: int):
        fila = con.execute("SELECT * FROM reservas WHERE ejemplar_id=? AND estado='ASIGNADA'",
                           (ejemplar_id,)).fetchone()
        return None if fila is None else ReservaDAO.desde_fila(fila)
