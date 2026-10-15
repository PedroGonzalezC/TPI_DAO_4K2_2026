"""Ficha bibliográfica de un título del catálogo."""

from dataclasses import dataclass


@dataclass
class Libro:
    id: int | None
    isbn: str
    titulo: str
    autor: str
    anio: int | None = None
