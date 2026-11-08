"""Entidad de dominio Multa."""

from dataclasses import dataclass
from datetime import datetime

from .excepciones import ReglaNegocio


@dataclass
class Multa:
    """Representa una multa económica generada por devolución tardía de un préstamo."""

    prestamo_id: int
    socio_id: int
    monto_centavos: int
    dias_atraso: int
    estado: str = "PENDIENTE"
    creada_en: str | None = None
    pagada_en: str | None = None
    id: int | None = None

    ESTADOS_VALIDOS = {"PENDIENTE", "PAGADA"}

    def __post_init__(self) -> None:
        if self.monto_centavos is None or int(self.monto_centavos) <= 0:
            raise ReglaNegocio("El monto de la multa debe ser mayor a cero")
        if self.dias_atraso is None or int(self.dias_atraso) <= 0:
            raise ReglaNegocio("Los días de atraso de la multa deben ser mayores a cero")
        self.monto_centavos = int(self.monto_centavos)
        self.dias_atraso = int(self.dias_atraso)
        self.estado = (self.estado or "PENDIENTE").strip().upper()
        if self.estado not in self.ESTADOS_VALIDOS:
            raise ReglaNegocio(f"Estado de multa inválido: {self.estado}")

    @property
    def esta_pendiente(self) -> bool:
        return self.estado == "PENDIENTE"

    def pagar(self, ahora: datetime) -> None:
        if self.estado != "PENDIENTE":
            raise ReglaNegocio("La multa ya se encuentra pagada")
        self.estado = "PAGADA"
        self.pagada_en = ahora.isoformat()
