"""Entidad de dominio EventoRemito."""

from dataclasses import dataclass


@dataclass
class EventoRemito:
    """Representa un evento dentro del historial de trazabilidad de un remito."""

    remito_id: int
    estado: str
    fecha: str
    detalle: str = ""
    id: int | None = None
