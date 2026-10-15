"""Préstamo cuya entrega ocurre en la sede de origen."""

from dataclasses import dataclass

from .prestamo import Prestamo


@dataclass(frozen=True)
class PrestamoLocal(Prestamo):
    @property
    def tipo(self) -> str:
        return "LOCAL"
