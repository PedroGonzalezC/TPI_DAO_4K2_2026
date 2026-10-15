from ...regla_negocio import ReglaNegocio
from .estado_ejemplar import EstadoEjemplar


class Baja(EstadoEjemplar):
    nombre = "BAJA"

    def avanzar(self, ejemplar, nuevo_estado):
        raise ReglaNegocio(f"Transición de ejemplar inválida: {self.nombre} -> {nuevo_estado}")
