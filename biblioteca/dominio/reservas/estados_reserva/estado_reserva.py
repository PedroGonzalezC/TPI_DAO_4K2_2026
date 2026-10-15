"""Contrato State para la asignación y el cierre de una reserva."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ...regla_negocio import ReglaNegocio

if TYPE_CHECKING:
    from ..reserva import Reserva


class EstadoReserva(ABC):
    nombre: str

    @abstractmethod
    def avanzar(self, reserva: "Reserva", nuevo_estado: str) -> None:
        """Valida la transición solicitada."""

    def _transicionar(self, reserva: "Reserva", nuevo_estado: str, *siguientes: "EstadoReserva") -> None:
        destino = next((estado for estado in siguientes if estado.nombre == nuevo_estado), None)
        if destino is None:
            raise ReglaNegocio(
                f"Transición de reserva inválida: {self.nombre} -> {nuevo_estado}"
            )
        reserva._estado = destino
