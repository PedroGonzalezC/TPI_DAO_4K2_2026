"""Entidad de dominio Reserva."""

from dataclasses import dataclass

from .excepciones import ReglaNegocio


@dataclass
class Reserva:
    """Reserva de un material para retiro en una sede."""

    socio_id: int
    libro_id: int
    sede_id: int
    creada_en: str
    estado: str = "EN_ESPERA"
    ejemplar_id: int | None = None
    id: int | None = None

    def asegurar_corresponde_a_solicitud(self, socio_id: int, sede_destino_id: int) -> None:
        if self.estado != "ASIGNADA" or self.socio_id != socio_id or self.sede_id != sede_destino_id:
            raise ReglaNegocio("El ejemplar está reservado para otro socio o sede de retiro")

    def asignar(self, ejemplar_id: int) -> None:
        if self.estado != "EN_ESPERA":
            raise ReglaNegocio("Solo se puede asignar una reserva en espera")
        self.estado = "ASIGNADA"
        self.ejemplar_id = ejemplar_id

    def cumplir(self) -> None:
        if self.estado != "ASIGNADA":
            raise ReglaNegocio("La reserva no está asignada")
        self.estado = "CUMPLIDA"

    def cancelar(self) -> int | None:
        if self.estado not in ("EN_ESPERA", "ASIGNADA"):
            raise ReglaNegocio("La reserva ya está cerrada")
        ejemplar_liberado = self.ejemplar_id
        self.estado = "CANCELADA"
        return ejemplar_liberado
