"""Contrato State para las transiciones de un préstamo."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ...regla_negocio import ReglaNegocio

if TYPE_CHECKING:
    from ..prestamo import Prestamo


class EstadoPrestamo(ABC):
    """Cada estado define cuáles son los avances válidos del préstamo."""

    nombre: str

    @abstractmethod
    def avanzar(self, prestamo: "Prestamo", nuevo_estado: str) -> None:
        """Valida y realiza la transición solicitada."""

    def _transicionar(self, prestamo: "Prestamo", nuevo_estado: str, siguiente: "EstadoPrestamo") -> None:
        if nuevo_estado != siguiente.nombre:
            raise ReglaNegocio(
                f"Transición de préstamo inválida: {self.nombre} -> {nuevo_estado}"
            )
        prestamo._estado = siguiente
