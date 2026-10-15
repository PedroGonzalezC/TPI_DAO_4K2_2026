"""Contrato State para el ciclo de vida de un ejemplar físico."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ...regla_negocio import ReglaNegocio

if TYPE_CHECKING:
    from ..ejemplar import Ejemplar


class EstadoEjemplar(ABC):
    nombre: str

    @abstractmethod
    def avanzar(self, ejemplar: "Ejemplar", nuevo_estado: str) -> None:
        """Valida y aplica una transición del ejemplar."""

    def _transicionar(self, ejemplar: "Ejemplar", nuevo_estado: str, *siguientes: "EstadoEjemplar") -> None:
        destino = next((estado for estado in siguientes if estado.nombre == nuevo_estado), None)
        if destino is None:
            raise ReglaNegocio(
                f"Transición de ejemplar inválida: {self.nombre} -> {nuevo_estado}"
            )
        ejemplar._estado = destino
