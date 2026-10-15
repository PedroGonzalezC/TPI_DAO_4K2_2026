from .estado_ejemplar import EstadoEjemplar


class Prestado(EstadoEjemplar):
    nombre = "PRESTADO"

    def avanzar(self, ejemplar, nuevo_estado):
        from .baja import Baja
        from .disponible import Disponible
        from .en_revision import EnRevision
        from .por_retornar import PorRetornar
        self._transicionar(
            ejemplar, nuevo_estado, Disponible(), EnRevision(), Baja(), PorRetornar()
        )
