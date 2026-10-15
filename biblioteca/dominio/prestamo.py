"""Datos comunes de los préstamos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Prestamo:
    socio_id: int
    ejemplar_id: int
    sede_origen_id: int
    sede_destino_id: int

    @property
    def tipo(self) -> str:
        raise NotImplementedError
