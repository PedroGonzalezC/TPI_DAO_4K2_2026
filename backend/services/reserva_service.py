"""Servicio de negocio para la gestión de reservas y cola de espera."""

import sqlite3

from ..daos.ejemplar_dao import EjemplarDAO
from ..daos.material_dao import MaterialDAO
from ..daos.reserva_dao import ReservaDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import NoEncontradoError, ReglaNegocio, normalizar_fecha
from ..models.reserva import Reserva
from .sede_service import SedeService
from .socio_service import SocioService


class ReservaService:
    """Gestiona reservas por orden de llegada y asignación automática de ejemplares."""

    def __init__(self, db: BaseDatos) -> None:
        self.db = db

    def asignar_si_corresponde(self, con: sqlite3.Connection, ejemplar_id: int) -> None:
        ejemplar_dao = EjemplarDAO(con)
        reserva_dao = ReservaDAO(con)
        ejemplar = ejemplar_dao.obtener_por_id(ejemplar_id)
        if ejemplar is None:
            raise NoEncontradoError(f"No existe ejemplare con id {ejemplar_id}")
        if not ejemplar.esta_disponible:
            return
        en_espera = reserva_dao.buscar_primera_en_espera_habilitada(
            ejemplar.libro_id, ejemplar.sede_actual_id
        )
        if en_espera is not None:
            en_espera.asignar(ejemplar_id)
            ejemplar.reservar()
            reserva_dao.actualizar(en_espera)
            ejemplar_dao.actualizar(ejemplar)

    def reservar(self, socio_id: int, libro_id: int, sede_id: int, *, fecha=None) -> int:
        ahora = normalizar_fecha(fecha)
        with self.db.conexion() as con:
            SocioService.obtener_habilitado(con, socio_id)
            if MaterialDAO(con).obtener_por_id(libro_id) is None:
                raise NoEncontradoError(f"No existe libro con id {libro_id}")
            SedeService.obtener_activa(con, sede_id)

            reserva = Reserva(
                socio_id=socio_id,
                libro_id=libro_id,
                sede_id=sede_id,
                creada_en=ahora.isoformat(),
            )
            try:
                reserva_id = ReservaDAO(con).crear(reserva)
            except sqlite3.IntegrityError as exc:
                raise ReglaNegocio(
                    "El socio ya tiene una reserva activa para ese libro y sede"
                ) from exc

            disponible = EjemplarDAO(con).buscar_disponible_en_sede(libro_id, sede_id)
            if disponible is not None and disponible.id is not None:
                self.asignar_si_corresponde(con, disponible.id)
            return reserva_id

    def cancelar_reserva(self, reserva_id: int) -> None:
        with self.db.conexion() as con:
            reserva_dao = ReservaDAO(con)
            reserva = reserva_dao.obtener_por_id(reserva_id)
            if reserva is None:
                raise NoEncontradoError(f"No existe reserva con id {reserva_id}")
            ejemplar_id = reserva.cancelar()
            reserva_dao.actualizar(reserva)
            if ejemplar_id is not None:
                ejemplar_dao = EjemplarDAO(con)
                ejemplar = ejemplar_dao.obtener_por_id(ejemplar_id)
                if ejemplar is None:
                    raise NoEncontradoError(f"No existe ejemplare con id {ejemplar_id}")
                ejemplar.liberar()
                ejemplar_dao.actualizar(ejemplar)
                self.asignar_si_corresponde(con, ejemplar_id)

    def listar_reservas(self) -> list[dict]:
        with self.db.conexion() as con:
            return ReservaDAO(con).listar()
