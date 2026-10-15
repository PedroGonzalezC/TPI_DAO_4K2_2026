"""Remito preparado para despacho."""

from .despachado import Despachado
from .estado_remito import EstadoRemito


class Empaquetado(EstadoRemito):
    nombre = "EMPAQUETADO"

    def avanzar(self, remito: "Remito", nuevo_estado: str) -> None:
        self._transicionar(remito, nuevo_estado, Despachado())
