from .estado_reserva import EstadoReserva


class EnEspera(EstadoReserva):
    nombre = "EN_ESPERA"

    def avanzar(self, reserva, nuevo_estado):
        from .asignada import Asignada
        from .cancelada import Cancelada
        self._transicionar(reserva, nuevo_estado, Asignada(), Cancelada())
