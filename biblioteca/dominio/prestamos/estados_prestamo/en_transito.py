"""Préstamo interbibliotecario cuyo remito de ida fue despachado."""

from .estado_prestamo import EstadoPrestamo
from .listo import Listo


class EnTransito(EstadoPrestamo):
    nombre = "EN_TRANSITO"

    def avanzar(self, prestamo: "Prestamo", nuevo_estado: str) -> None:
        self._transicionar(prestamo, nuevo_estado, Listo())
