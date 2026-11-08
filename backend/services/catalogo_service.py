"""Servicio de negocio para materiales bibliográficos, ejemplares y disponibilidad."""

import sqlite3

from ..daos.ejemplar_dao import EjemplarDAO
from ..daos.material_dao import MaterialDAO
from ..database.conexion import BaseDatos
from ..models.ejemplar import Ejemplar
from ..models.excepciones import NoEncontradoError, ReglaNegocio
from ..models.material import Material
from .reserva_service import ReservaService
from .sede_service import SedeService


class CatalogoService:
    """Gestiona fichas de materiales (libros), ejemplares físicos, revisión y disponibilidad."""

    def __init__(self, db: BaseDatos, reserva_service: ReservaService) -> None:
        self.db = db
        self.reserva_service = reserva_service

    @staticmethod
    def obtener_material_existente(con: sqlite3.Connection, libro_id: int) -> Material:
        material = MaterialDAO(con).obtener_por_id(libro_id)
        if material is None:
            raise NoEncontradoError(f"No existe libro con id {libro_id}")
        return material

    @staticmethod
    def obtener_ejemplar_existente(con: sqlite3.Connection, ejemplar_id: int) -> Ejemplar:
        ejemplar = EjemplarDAO(con).obtener_por_id(ejemplar_id)
        if ejemplar is None:
            raise NoEncontradoError(f"No existe ejemplare con id {ejemplar_id}")
        return ejemplar

    def crear_material(
        self, isbn: str, titulo: str, autor: str, anio: int | None = None
    ) -> int:
        material = Material(isbn=isbn, titulo=titulo, autor=autor, anio=anio)
        with self.db.conexion() as con:
            try:
                return MaterialDAO(con).crear(material)
            except sqlite3.IntegrityError as exc:
                raise ReglaNegocio("Ya existe un libro con ese ISBN") from exc

    crear_libro = crear_material

    def actualizar_material(
        self,
        libro_id: int,
        *,
        titulo: str | None = None,
        autor: str | None = None,
        anio: int | None = None,
    ) -> None:
        with self.db.conexion() as con:
            material = self.obtener_material_existente(con, libro_id)
            material.actualizar(titulo=titulo, autor=autor, anio=anio)
            MaterialDAO(con).actualizar(material)

    actualizar_libro = actualizar_material

    def listar_materiales(self) -> list[dict]:
        with self.db.conexion() as con:
            return MaterialDAO(con).listar()

    listar_libros = listar_materiales

    def crear_ejemplar(self, codigo: str, libro_id: int, sede_id: int) -> int:
        ejemplar = Ejemplar(
            codigo=codigo,
            libro_id=libro_id,
            sede_pertenencia_id=sede_id,
            sede_actual_id=sede_id,
        )
        with self.db.conexion() as con:
            self.obtener_material_existente(con, libro_id)
            SedeService.obtener_activa(con, sede_id)
            try:
                return EjemplarDAO(con).crear(ejemplar)
            except sqlite3.IntegrityError as exc:
                raise ReglaNegocio("Ya existe un ejemplar con ese código") from exc

    def listar_ejemplares(self) -> list[dict]:
        with self.db.conexion() as con:
            return EjemplarDAO(con).listar()

    def disponibilidad(self, sede_id: int | None = None) -> list[dict]:
        with self.db.conexion() as con:
            if sede_id is not None:
                SedeService.obtener_existente(con, sede_id)
            return EjemplarDAO(con).consultar_disponibilidad(sede_id)

    def cerrar_revision(self, ejemplar_id: int, apto: bool) -> None:
        with self.db.conexion() as con:
            ejemplar_dao = EjemplarDAO(con)
            ejemplar = self.obtener_ejemplar_existente(con, ejemplar_id)
            ejemplar.cerrar_revision(apto)
            ejemplar_dao.actualizar(ejemplar)
            if apto:
                self.reserva_service.asignar_si_corresponde(con, ejemplar_id)
