"""Préstamo cuyo retiro se hace en la sede de pertenencia."""

from .prestamo import Prestamo


class PrestamoLocal(Prestamo):
    @property
    def tipo(self) -> str:
        return "LOCAL"
