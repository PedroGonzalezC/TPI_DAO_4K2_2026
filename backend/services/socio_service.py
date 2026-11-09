"""Servicio de negocio para el padrón de socios."""

import sqlite3

from ..daos.multa_dao import MultaDAO
from ..daos.socio_dao import SocioDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import NoEncontradoError, ReglaNegocio
from ..models.socio import Socio


class SocioService:
    """Gestiona altas, ediciones, habilitación/inhabilitación y consultas de socios."""

    def __init__(self, db: BaseDatos) -> None:
        self.db = db

    @staticmethod
    def obtener_existente(con: sqlite3.Connection, socio_id: int) -> Socio:
        socio = SocioDAO(con).obtener_por_id(socio_id)
        if socio is None:
            raise NoEncontradoError(f"No existe socio con id {socio_id}")
        return socio

    @classmethod
    def obtener_habilitado(cls, con: sqlite3.Connection, socio_id: int) -> Socio:
        socio = cls.obtener_existente(con, socio_id)
        if MultaDAO(con).tiene_pendientes_por_socio(socio_id):
            raise ReglaNegocio(
                f"El socio {socio_id} posee multas pendientes de pago y está inhabilitado"
            )
        socio.asegurar_habilitado()
        return socio

    def crear_socio(self, documento: str, nombre: str, email: str) -> int:
        socio = Socio(documento=documento, nombre=nombre, email=email)
        with self.db.conexion() as con:
            try:
                return SocioDAO(con).crear(socio)
            except sqlite3.IntegrityError as exc:
                raise ReglaNegocio("Ya existe un socio con ese documento") from exc

    def actualizar_socio(
        self,
        socio_id: int,
        *,
        nombre: str | None = None,
        email: str | None = None,
        habilitado: bool | int | None = None,
    ) -> None:
        with self.db.conexion() as con:
            socio = self.obtener_existente(con, socio_id)
            if bool(habilitado) and MultaDAO(con).tiene_pendientes_por_socio(socio_id):
                raise ReglaNegocio(
                    "No se puede habilitar al socio mientras posea multas pendientes de pago"
                )
            socio.actualizar(nombre=nombre, email=email, habilitado=habilitado)
            SocioDAO(con).actualizar(socio)

    def listar_socios(self) -> list[dict]:
        with self.db.conexion() as con:
            return SocioDAO(con).listar()

    def eliminar_socio(self, socio_id: int) -> str:
        with self.db.conexion() as con:
            socio_dao = SocioDAO(con)
            socio = self.obtener_existente(con, socio_id)
            if socio_dao.tiene_prestamos_activos(socio_id):
                raise ReglaNegocio(
                    "No se puede dar de baja ni eliminar un socio con préstamos en curso"
                )
            if socio_dao.tiene_historial(socio_id):
                socio.actualizar(habilitado=False)
                socio_dao.actualizar(socio)
                return "baja_logica"
            socio_dao.eliminar(socio_id)
            return "eliminado"
