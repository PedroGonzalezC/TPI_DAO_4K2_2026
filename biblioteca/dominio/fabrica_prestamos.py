"""Selección del tipo de préstamo según las sedes."""

from .prestamo import Prestamo
from .prestamo_local import PrestamoLocal
from .prestamo_interbibliotecario import PrestamoInterbibliotecario


class FabricaPrestamos:
    """Fábrica simple: el caso de uso no instancia las clases concretas."""

    @staticmethod
    def crear(socio_id: int, ejemplar_id: int, origen: int, destino: int) -> Prestamo:
        clase = PrestamoLocal if origen == destino else PrestamoInterbibliotecario
        return clase(socio_id, ejemplar_id, origen, destino)
