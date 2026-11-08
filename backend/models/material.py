"""Entidad de dominio Material (Libro)."""

from dataclasses import dataclass

from .excepciones import ReglaNegocio, validar_texto_obligatorio


@dataclass
class Material:
    """Ficha bibliográfica del catálogo (Libro / Material de consulta)."""

    isbn: str
    titulo: str
    autor: str
    anio: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.isbn = validar_texto_obligatorio(self.isbn, "ISBN")
        self.titulo = validar_texto_obligatorio(self.titulo, "Título")
        self.autor = validar_texto_obligatorio(self.autor, "Autor")
        self._validar_anio(self.anio)

    @staticmethod
    def _validar_anio(anio: int | None) -> None:
        if anio is not None and (not isinstance(anio, int) or isinstance(anio, bool) or anio <= 0):
            raise ReglaNegocio("El año debe ser positivo")

    def actualizar(
        self,
        *,
        titulo: str | None = None,
        autor: str | None = None,
        anio: int | None = None,
    ) -> None:
        self._validar_anio(anio)
        if titulo is not None:
            self.titulo = validar_texto_obligatorio(titulo, "Título")
        if autor is not None:
            self.autor = validar_texto_obligatorio(autor, "Autor")
        if anio is not None:
            self.anio = anio


Libro = Material
