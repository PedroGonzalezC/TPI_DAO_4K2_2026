"""Factory para crear el tipo de préstamo apropiado."""

from .prestamo import Prestamo
from .prestamo_interbibliotecario import PrestamoInterbibliotecario
from .prestamo_local import PrestamoLocal


class FabricaPrestamos:
    """Oculta la elección entre préstamo local e interbibliotecario."""

    @staticmethod
    def crear(socio_id: int, ejemplar_id: int, origen: int, destino: int,
              estado: str = "SOLICITADO") -> Prestamo:
        clase = PrestamoLocal if origen == destino else PrestamoInterbibliotecario
        return clase(socio_id, ejemplar_id, origen, destino, estado)
