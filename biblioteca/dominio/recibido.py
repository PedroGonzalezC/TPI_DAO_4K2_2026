"""Estado terminal del remito."""

from .estado_remito import EstadoRemito
from .regla_negocio import ReglaNegocio


class Recibido(EstadoRemito):
    nombre = "RECIBIDO"

    def avanzar(self, remito: "Remito", nuevo_estado: str) -> None:
        raise ReglaNegocio(f"Transición de remito inválida: {self.nombre} -> {nuevo_estado}")
