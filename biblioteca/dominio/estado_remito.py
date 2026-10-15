"""Contrato del patrón State para el remito."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .regla_negocio import ReglaNegocio

if TYPE_CHECKING:
    from .remito import Remito


class EstadoRemito(ABC):
    """Cada etapa decide cuál es la única transición permitida."""

    nombre: str

    @abstractmethod
    def avanzar(self, remito: "Remito", nuevo_estado: str) -> None:
        """Valida y realiza la transición del remito."""

    def _transicionar(self, remito: "Remito", nuevo_estado: str, siguiente: "EstadoRemito") -> None:
        if nuevo_estado != siguiente.nombre:
            raise ReglaNegocio(f"Transición de remito inválida: {self.nombre} -> {nuevo_estado}")
        remito._estado = siguiente
