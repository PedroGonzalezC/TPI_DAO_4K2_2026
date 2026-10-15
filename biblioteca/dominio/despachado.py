"""Remito en tránsito hacia la sede de destino."""

from .estado_remito import EstadoRemito
from .recibido import Recibido


class Despachado(EstadoRemito):
    nombre = "DESPACHADO"

    def avanzar(self, remito: "Remito", nuevo_estado: str) -> None:
        self._transicionar(remito, nuevo_estado, Recibido())
