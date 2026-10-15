"""Estado inicial del remito."""

from .empaquetado import Empaquetado
from .estado_remito import EstadoRemito


class Creado(EstadoRemito):
    nombre = "CREADO"

    def avanzar(self, remito: "Remito", nuevo_estado: str) -> None:
        self._transicionar(remito, nuevo_estado, Empaquetado())
