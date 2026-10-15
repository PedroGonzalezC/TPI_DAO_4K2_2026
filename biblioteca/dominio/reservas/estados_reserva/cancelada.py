from ...regla_negocio import ReglaNegocio
from .estado_reserva import EstadoReserva


class Cancelada(EstadoReserva):
    nombre = "CANCELADA"

    def avanzar(self, reserva, nuevo_estado):
        raise ReglaNegocio(f"Transición de reserva inválida: {self.nombre} -> {nuevo_estado}")
