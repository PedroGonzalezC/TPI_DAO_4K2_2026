"""Reserva de un libro en una sede y contexto State."""

from dataclasses import dataclass, field

from ..regla_negocio import ReglaNegocio
from .estados_reserva.asignada import Asignada
from .estados_reserva.cancelada import Cancelada
from .estados_reserva.cumplida import Cumplida
from .estados_reserva.en_espera import EnEspera


ESTADOS_RESERVA = {clase.nombre: clase for clase in (EnEspera, Asignada, Cumplida, Cancelada)}


@dataclass
class Reserva:
    id: int | None
    socio_id: int
    libro_id: int
    sede_id: int
    creada_en: str
    ejemplar_id: int | None = None
    estado: str = "EN_ESPERA"
    _estado: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            self._estado = ESTADOS_RESERVA[self.estado]()
        except KeyError as exc:
            raise ReglaNegocio(f"Estado de reserva desconocido: {self.estado}") from exc

    def avanzar(self, nuevo_estado: str) -> None:
        self._estado.avanzar(self, nuevo_estado)
        self.estado = self._estado.nombre

    def asignar_ejemplar(self, ejemplar_id: int) -> None:
        self.avanzar("ASIGNADA")
        self.ejemplar_id = ejemplar_id
