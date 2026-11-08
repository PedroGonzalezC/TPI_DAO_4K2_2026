"""Servicio de negocio para logística de traslados y eventos del remito."""

import sqlite3
from datetime import datetime

from ..daos.ejemplar_dao import EjemplarDAO
from ..daos.evento_remito_dao import EventoRemitoDAO
from ..daos.prestamo_dao import PrestamoDAO
from ..daos.remito_dao import RemitoDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import NoEncontradoError, normalizar_fecha
from ..models.remito import Remito
from .catalogo_service import CatalogoService
from .reserva_service import ReservaService
from .sede_service import SedeService


class RemitoService:
    """Gestiona transiciones de remitos, trazabilidad (Observer) y coherencia con préstamos."""

    def __init__(self, db: BaseDatos, reserva_service: ReservaService) -> None:
        self.db = db
        self.reserva_service = reserva_service

    @staticmethod
    def crear_remito_con_evento_inicial(
        con: sqlite3.Connection,
        *,
        prestamo_id: int,
        ejemplar_id: int,
        tipo: str,
        origen_id: int,
        destino_id: int,
        fecha: datetime,
    ) -> int:
        fecha_iso = fecha.isoformat()
        remito = Remito(
            id=None,
            estado="CREADO",
            prestamo_id=prestamo_id,
            ejemplar_id=ejemplar_id,
            tipo=tipo,
            origen_id=origen_id,
            destino_id=destino_id,
            creado_en=fecha_iso,
        )
        remito.id = RemitoDAO(con).crear(remito)
        remito.suscribir(EventoRemitoDAO(con))
        remito.registrar_creacion(fecha, "Remito generado")
        return remito.id

    def avanzar_remito(
        self, remito_id: int, nuevo_estado: str, *, fecha=None, detalle: str = ""
    ) -> None:
        ahora = normalizar_fecha(fecha)
        with self.db.conexion() as con:
            remito_dao = RemitoDAO(con)
            evento_dao = EventoRemitoDAO(con)
            ejemplar_dao = EjemplarDAO(con)
            prestamo_dao = PrestamoDAO(con)

            remito = remito_dao.obtener_por_id(remito_id)
            if remito is None:
                raise NoEncontradoError(f"No existe remito con id {remito_id}")

            ultimo_evento = evento_dao.obtener_ultimo_por_remito(remito_id)
            ultima_fecha_iso = ultimo_evento.fecha if ultimo_evento is not None else None

            if remito.requiere_sedes_activas(nuevo_estado):
                if remito.origen_id is not None:
                    SedeService.obtener_activa(con, remito.origen_id)
                if remito.destino_id is not None:
                    SedeService.obtener_activa(con, remito.destino_id)

            remito.suscribir(evento_dao)
            remito.avanzar(
                nuevo_estado,
                ahora,
                detalle,
                ultima_fecha_iso=ultima_fecha_iso,
            )
            remito_dao.actualizar(remito)

            ejemplar = CatalogoService.obtener_ejemplar_existente(con, remito.ejemplar_id)
            prestamo = prestamo_dao.obtener_por_id(remito.prestamo_id)
            if prestamo is None:
                raise NoEncontradoError(f"No existe prestamo con id {remito.prestamo_id}")

            if nuevo_estado == "DESPACHADO":
                ejemplar.despachar()
                ejemplar_dao.actualizar(ejemplar)
                if remito.tipo == "IDA":
                    prestamo.marcar_en_transito()
                    prestamo_dao.actualizar(prestamo)
            elif nuevo_estado == "RECIBIDO":
                if remito.tipo == "IDA":
                    ejemplar.recibir_en(remito.destino_id, "APARTADO")
                    ejemplar_dao.actualizar(ejemplar)
                    prestamo.marcar_listo()
                    prestamo_dao.actualizar(prestamo)
                else:
                    estado_final = prestamo.estado_ejemplar_al_recibir_retorno()
                    ejemplar.recibir_en(remito.destino_id, estado_final)
                    ejemplar_dao.actualizar(ejemplar)
                    if estado_final == "DISPONIBLE":
                        self.reserva_service.asignar_si_corresponde(con, ejemplar.id)

    def historial_remito(self, remito_id: int) -> list[dict]:
        with self.db.conexion() as con:
            if RemitoDAO(con).obtener_por_id(remito_id) is None:
                raise NoEncontradoError(f"No existe remito con id {remito_id}")
            return EventoRemitoDAO(con).listar_por_remito(remito_id)

    def listar_remitos(self) -> list[dict]:
        with self.db.conexion() as con:
            return RemitoDAO(con).listar()
