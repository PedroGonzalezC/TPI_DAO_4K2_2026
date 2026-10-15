"""Contrato de notificación para las transiciones del remito."""

from typing import Protocol


class ObservadorRemito(Protocol):
    def actualizar(self, remito_id: int, estado: str, fecha: str, detalle: str) -> None: ...
