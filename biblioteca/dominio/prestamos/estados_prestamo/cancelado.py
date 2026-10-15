"""Estado terminal reservado para futuras cancelaciones."""

from ...regla_negocio import ReglaNegocio
from .estado_prestamo import EstadoPrestamo


class Cancelado(EstadoPrestamo):
    nombre = "CANCELADO"

    def avanzar(self, prestamo: "Prestamo", nuevo_estado: str) -> None:
        raise ReglaNegocio(f"Transición de préstamo inválida: {self.nombre} -> {nuevo_estado}")
