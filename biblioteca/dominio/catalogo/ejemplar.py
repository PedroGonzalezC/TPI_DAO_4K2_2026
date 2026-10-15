"""Copia física de un libro y contexto State de su disponibilidad."""

from dataclasses import dataclass, field

from ..regla_negocio import ReglaNegocio
from .estados_ejemplar.apartado import Apartado
from .estados_ejemplar.baja import Baja
from .estados_ejemplar.disponible import Disponible
from .estados_ejemplar.en_revision import EnRevision
from .estados_ejemplar.en_transito import EnTransito
from .estados_ejemplar.por_retornar import PorRetornar
from .estados_ejemplar.prestado import Prestado
from .estados_ejemplar.reservado import Reservado


ESTADOS_EJEMPLAR = {
    clase.nombre: clase for clase in (
        Disponible, Apartado, Reservado, Prestado, EnTransito, PorRetornar, EnRevision, Baja
    )
}


@dataclass
class Ejemplar:
    id: int | None
    codigo: str
    libro_id: int
    sede_pertenencia_id: int
    sede_actual_id: int
    estado: str = "DISPONIBLE"
    _estado: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            self._estado = ESTADOS_EJEMPLAR[self.estado]()
        except KeyError as exc:
            raise ReglaNegocio(f"Estado de ejemplar desconocido: {self.estado}") from exc

    def avanzar(self, nuevo_estado: str) -> None:
        self._estado.avanzar(self, nuevo_estado)
        self.estado = self._estado.nombre

    def ubicar_en(self, sede_id: int) -> None:
        self.sede_actual_id = sede_id
