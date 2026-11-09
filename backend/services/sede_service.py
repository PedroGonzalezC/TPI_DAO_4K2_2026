"""Servicio de negocio para la administración de sedes."""

import sqlite3

from ..daos.sede_dao import SedeDAO
from ..database.conexion import BaseDatos
from ..models.excepciones import NoEncontradoError, ReglaNegocio
from ..models.sede import Sede


class SedeService:
    """Gestiona altas, modificaciones, bajas lógicas y consultas de sedes."""

    def __init__(self, db: BaseDatos) -> None:
        self.db = db

    @staticmethod
    def obtener_existente(con: sqlite3.Connection, sede_id: int) -> Sede:
        sede = SedeDAO(con).obtener_por_id(sede_id)
        if sede is None:
            raise NoEncontradoError(f"No existe sede con id {sede_id}")
        return sede

    @classmethod
    def obtener_activa(cls, con: sqlite3.Connection, sede_id: int) -> Sede:
        sede = cls.obtener_existente(con, sede_id)
        sede.asegurar_activa()
        return sede

    def crear_sede(self, nombre: str, direccion: str, contacto: str, horarios: str) -> int:
        sede = Sede(nombre=nombre, direccion=direccion, contacto=contacto, horarios=horarios)
        with self.db.conexion() as con:
            try:
                return SedeDAO(con).crear(sede)
            except sqlite3.IntegrityError as exc:
                raise ReglaNegocio("Ya existe una sede con ese nombre") from exc

    def actualizar_sede(
        self,
        sede_id: int,
        *,
        direccion: str | None = None,
        contacto: str | None = None,
        horarios: str | None = None,
        activa: bool | int | None = None,
    ) -> None:
        with self.db.conexion() as con:
            sede = self.obtener_existente(con, sede_id)
            sede.actualizar(
                direccion=direccion,
                contacto=contacto,
                horarios=horarios,
                activa=activa,
            )
            SedeDAO(con).actualizar(sede)

    def listar_sedes(self) -> list[dict]:
        with self.db.conexion() as con:
            return SedeDAO(con).listar()

    def eliminar_sede(self, sede_id: int) -> str:
        with self.db.conexion() as con:
            sede_dao = SedeDAO(con)
            sede = self.obtener_existente(con, sede_id)
            if sede_dao.tiene_dependencias(sede_id):
                sede.actualizar(activa=False)
                sede_dao.actualizar(sede)
                return "baja_logica"
            sede_dao.eliminar(sede_id)
            return "eliminado"
