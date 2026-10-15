"""Estado terminal de un préstamo devuelto."""

from ...regla_negocio import ReglaNegocio
from .estado_prestamo import EstadoPrestamo


class Devuelto(EstadoPrestamo):
    nombre = "DEVUELTO"

    def avanzar(self, prestamo: "Prestamo", nuevo_estado: str) -> None:
        raise ReglaNegocio(f"Transición de préstamo inválida: {self.nombre} -> {nuevo_estado}")
