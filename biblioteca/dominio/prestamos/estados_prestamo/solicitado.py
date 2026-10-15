"""Estado inicial de un préstamo."""

from ...regla_negocio import ReglaNegocio
from .activo import Activo
from .en_transito import EnTransito
from .estado_prestamo import EstadoPrestamo


class Solicitado(EstadoPrestamo):
    nombre = "SOLICITADO"

    def avanzar(self, prestamo: "Prestamo", nuevo_estado: str) -> None:
        if prestamo.tipo == "LOCAL":
            self._transicionar(prestamo, nuevo_estado, Activo())
            return
        if prestamo.tipo == "INTERBIBLIOTECARIO":
            self._transicionar(prestamo, nuevo_estado, EnTransito())
            return
        raise ReglaNegocio(f"Tipo de préstamo desconocido: {prestamo.tipo}")
