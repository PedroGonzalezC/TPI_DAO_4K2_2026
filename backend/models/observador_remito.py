"""Interfaz/Protocolo del patrón Observer para eventos del remito."""

from typing import Protocol


class ObservadorRemito(Protocol):
    """Contrato que debe cumplir cualquier observador suscripto a un Remito."""

    def actualizar(self, remito_id: int, estado: str, fecha: str, detalle: str) -> None: ...
