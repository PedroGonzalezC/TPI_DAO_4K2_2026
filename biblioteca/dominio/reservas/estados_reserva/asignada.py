from .estado_reserva import EstadoReserva


class Asignada(EstadoReserva):
    nombre = "ASIGNADA"

    def avanzar(self, reserva, nuevo_estado):
        from .cancelada import Cancelada
        from .cumplida import Cumplida
        self._transicionar(reserva, nuevo_estado, Cumplida(), Cancelada())
