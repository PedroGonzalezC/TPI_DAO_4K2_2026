"""Estado inicial del remito."""

from .estado_remito import EstadoRemito
from .empaquetado import Empaquetado


class Creado(EstadoRemito):
    nombre = "CREADO"

    def avanzar(self, remito: "Remito", nuevo_estado: str) -> None:
        self._transicionar(remito, nuevo_estado, Empaquetado())
