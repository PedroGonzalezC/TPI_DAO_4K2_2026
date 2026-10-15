"""Préstamo interbibliotecario recibido y listo para entregar."""

from .activo import Activo
from .estado_prestamo import EstadoPrestamo


class Listo(EstadoPrestamo):
    nombre = "LISTO"

    def avanzar(self, prestamo: "Prestamo", nuevo_estado: str) -> None:
        self._transicionar(prestamo, nuevo_estado, Activo())
