from .estado_ejemplar import EstadoEjemplar


class EnTransito(EstadoEjemplar):
    nombre = "EN_TRANSITO"

    def avanzar(self, ejemplar, nuevo_estado):
        from .disponible import Disponible
        from .en_revision import EnRevision
        from .apartado import Apartado
        self._transicionar(ejemplar, nuevo_estado, Apartado(), Disponible(), EnRevision())
