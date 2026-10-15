from .estado_ejemplar import EstadoEjemplar


class PorRetornar(EstadoEjemplar):
    nombre = "POR_RETORNAR"

    def avanzar(self, ejemplar, nuevo_estado):
        from .en_transito import EnTransito
        self._transicionar(ejemplar, nuevo_estado, EnTransito())
