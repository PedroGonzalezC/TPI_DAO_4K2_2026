"""Remito: contexto State y emisor Observer."""

from dataclasses import dataclass, field
from datetime import datetime

from ..regla_negocio import ReglaNegocio
from .estados_remito.creado import Creado
from .estados_remito.despachado import Despachado
from .estados_remito.empaquetado import Empaquetado
from .estados_remito.recibido import Recibido
from .observador_remito import ObservadorRemito


ESTADOS_REMITO = {clase.nombre: clase for clase in (Creado, Empaquetado, Despachado, Recibido)}


@dataclass
class Remito:
    id: int
    estado: str
    observadores: list[ObservadorRemito] = field(default_factory=list)

    def __post_init__(self) -> None:
        try:
            self._estado = ESTADOS_REMITO[self.estado]()
        except KeyError as exc:
            raise ReglaNegocio(f"Estado de remito desconocido: {self.estado}") from exc

    def suscribir(self, observador: ObservadorRemito) -> None:
        self.observadores.append(observador)

    def avanzar(self, nuevo_estado: str, fecha: datetime, detalle: str = "") -> None:
        self._estado.avanzar(self, nuevo_estado)
        self.estado = self._estado.nombre
        for observador in self.observadores:
            observador.actualizar(self.id, self.estado, fecha.isoformat(timespec="seconds"), detalle)
