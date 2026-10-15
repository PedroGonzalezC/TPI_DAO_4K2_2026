from .estado_ejemplar import EstadoEjemplar


class Apartado(EstadoEjemplar):
    nombre = "APARTADO"

    def avanzar(self, ejemplar, nuevo_estado):
        from .en_transito import EnTransito
        from .prestado import Prestado
        self._transicionar(ejemplar, nuevo_estado, EnTransito(), Prestado())
