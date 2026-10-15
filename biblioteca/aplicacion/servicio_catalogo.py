"""Casos de uso de libros, ejemplares y disponibilidad."""

import sqlite3

from ..dominio.catalogo.ejemplar import Ejemplar
from ..dominio.catalogo.libro import Libro
from ..dominio.regla_negocio import ReglaNegocio
from ..persistencia.catalogo_dao import CatalogoDAO
from ..persistencia.ejemplar_dao import EjemplarDAO
from ..persistencia.libro_dao import LibroDAO
from ..persistencia.sede_dao import SedeDAO


class ServicioCatalogo:
    @staticmethod
    def _texto(valor, nombre: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ReglaNegocio(f"{nombre} es obligatorio")
        return valor.strip()

    @staticmethod
    def _unico(operacion, mensaje):
        try:
            return operacion()
        except sqlite3.IntegrityError as exc:
            raise ReglaNegocio(mensaje) from exc

    def crear_libro(self, con, isbn, titulo, autor, anio=None) -> int:
        if anio is not None and (not isinstance(anio, int) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")
        libro = Libro(None, self._texto(isbn, "ISBN"), self._texto(titulo, "Título"),
                      self._texto(autor, "Autor"), anio)
        return self._unico(lambda: LibroDAO.crear(con, libro), "Ya existe un libro con ese ISBN")

    def actualizar_libro(self, con, libro_id, *, titulo=None, autor=None, anio=None) -> None:
        if anio is not None and (not isinstance(anio, int) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")
        libro = LibroDAO.obtener(con, libro_id)
        libro.titulo = self._texto(titulo, "Título") if titulo is not None else libro.titulo
        libro.autor = self._texto(autor, "Autor") if autor is not None else libro.autor
        libro.anio = anio if anio is not None else libro.anio
        LibroDAO.guardar(con, libro)

    def crear_ejemplar(self, con, codigo, libro_id, sede_id) -> int:
        LibroDAO.obtener(con, libro_id)
        SedeDAO.obtener(con, sede_id).exigir_activa()
        ejemplar = Ejemplar(None, self._texto(codigo, "Código"), libro_id, sede_id, sede_id)
        return self._unico(lambda: EjemplarDAO.crear(con, ejemplar), "Ya existe un ejemplar con ese código")

    @staticmethod
    def disponibilidad(con, sede_id=None):
        if sede_id is not None:
            SedeDAO.obtener(con, sede_id)
        return CatalogoDAO.disponibilidad(con, sede_id)
