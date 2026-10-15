from .estado_ejemplar import EstadoEjemplar


class Disponible(EstadoEjemplar):
    nombre = "DISPONIBLE"

    def avanzar(self, ejemplar, nuevo_estado):
        from .apartado import Apartado
        from .reservado import Reservado
        self._transicionar(ejemplar, nuevo_estado, Apartado(), Reservado())
