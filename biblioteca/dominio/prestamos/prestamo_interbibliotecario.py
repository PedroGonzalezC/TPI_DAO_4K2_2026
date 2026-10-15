"""Préstamo que requiere trasladar el ejemplar entre sedes."""

from .prestamo import Prestamo


class PrestamoInterbibliotecario(Prestamo):
    @property
    def tipo(self) -> str:
        return "INTERBIBLIOTECARIO"
