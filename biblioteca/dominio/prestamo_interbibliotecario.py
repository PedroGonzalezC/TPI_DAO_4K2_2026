"""Préstamo que requiere un remito entre sedes."""

from dataclasses import dataclass

from .prestamo import Prestamo


@dataclass(frozen=True)
class PrestamoInterbibliotecario(Prestamo):
    @property
    def tipo(self) -> str:
        return "INTERBIBLIOTECARIO"
