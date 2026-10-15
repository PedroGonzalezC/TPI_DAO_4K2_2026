"""Estado terminal del remito."""

from ...regla_negocio import ReglaNegocio
from .estado_remito import EstadoRemito


class Recibido(EstadoRemito):
    nombre = "RECIBIDO"

    def avanzar(self, remito: "Remito", nuevo_estado: str) -> None:
        raise ReglaNegocio(f"Transición de remito inválida: {self.nombre} -> {nuevo_estado}")
