from .estado_ejemplar import EstadoEjemplar


class EnRevision(EstadoEjemplar):
    nombre = "EN_REVISION"

    def avanzar(self, ejemplar, nuevo_estado):
        from .baja import Baja
        from .disponible import Disponible
        self._transicionar(ejemplar, nuevo_estado, Disponible(), Baja())
