"""Préstamo entregado al socio."""

from .devuelto import Devuelto
from .estado_prestamo import EstadoPrestamo


class Activo(EstadoPrestamo):
    nombre = "ACTIVO"

    def avanzar(self, prestamo: "Prestamo", nuevo_estado: str) -> None:
        self._transicionar(prestamo, nuevo_estado, Devuelto())
