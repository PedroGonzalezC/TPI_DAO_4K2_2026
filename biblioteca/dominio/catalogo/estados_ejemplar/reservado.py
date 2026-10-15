from .estado_ejemplar import EstadoEjemplar


class Reservado(EstadoEjemplar):
    nombre = "RESERVADO"

    def avanzar(self, ejemplar, nuevo_estado):
        from .apartado import Apartado
        from .disponible import Disponible
        self._transicionar(ejemplar, nuevo_estado, Apartado(), Disponible())
