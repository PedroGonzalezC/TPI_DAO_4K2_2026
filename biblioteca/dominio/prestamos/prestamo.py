"""Contexto State para préstamos."""

from dataclasses import dataclass, field

from ..regla_negocio import ReglaNegocio
from .estados_prestamo.activo import Activo
from .estados_prestamo.cancelado import Cancelado
from .estados_prestamo.devuelto import Devuelto
from .estados_prestamo.en_transito import EnTransito
from .estados_prestamo.listo import Listo
from .estados_prestamo.solicitado import Solicitado


ESTADOS_PRESTAMO = {
    clase.nombre: clase
    for clase in (Solicitado, EnTransito, Listo, Activo, Devuelto, Cancelado)
}


@dataclass
class Prestamo:
    socio_id: int
    ejemplar_id: int
    sede_origen_id: int
    sede_destino_id: int
    estado: str = "SOLICITADO"
    _estado: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            self._estado = ESTADOS_PRESTAMO[self.estado]()
        except KeyError as exc:
            raise ReglaNegocio(f"Estado de préstamo desconocido: {self.estado}") from exc

    @property
    def tipo(self) -> str:
        raise NotImplementedError

    def avanzar(self, nuevo_estado: str) -> None:
        self._estado.avanzar(self, nuevo_estado)
        self.estado = self._estado.nombre
