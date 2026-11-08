"""Entidad de dominio Remito (Sujeto observable del patrón Observer)."""

from dataclasses import dataclass, field
from datetime import datetime

from .excepciones import ReglaNegocio
from .observador_remito import ObservadorRemito


@dataclass
class Remito:
    """Sujeto del patrón Observer y responsable de validar sus transiciones de estado."""

    id: int | None
    estado: str
    observadores: list[ObservadorRemito] = field(default_factory=list)
    prestamo_id: int | None = None
    ejemplar_id: int | None = None
    tipo: str | None = None
    origen_id: int | None = None
    destino_id: int | None = None
    creado_en: str | None = None
    recibido_en: str | None = None

    TRANSICIONES = {
        "CREADO": "EMPAQUETADO",
        "EMPAQUETADO": "DESPACHADO",
        "DESPACHADO": "RECIBIDO",
    }

    def suscribir(self, observador: ObservadorRemito) -> None:
        self.observadores.append(observador)

    def notificar(self, estado: str, fecha_iso: str, detalle: str = "") -> None:
        for observador in self.observadores:
            observador.actualizar(self.id, estado, fecha_iso, detalle)

    def registrar_creacion(self, fecha: datetime, detalle: str = "Remito generado") -> None:
        fecha_iso = fecha.isoformat(timespec="seconds")
        self.notificar(self.estado, fecha_iso, detalle)

    def requiere_sedes_activas(self, nuevo_estado: str) -> bool:
        return nuevo_estado in {"EMPAQUETADO", "DESPACHADO"}

    def avanzar(
        self,
        nuevo_estado: str,
        fecha: datetime,
        detalle: str = "",
        *,
        ultima_fecha_iso: str | None = None,
    ) -> None:
        if ultima_fecha_iso is not None and fecha < datetime.fromisoformat(ultima_fecha_iso):
            raise ReglaNegocio("El evento no puede preceder al estado anterior del remito")
        if self.TRANSICIONES.get(self.estado) != nuevo_estado:
            raise ReglaNegocio(f"Transición de remito inválida: {self.estado} -> {nuevo_estado}")
        self.estado = nuevo_estado
        fecha_iso = fecha.isoformat(timespec="seconds")
        if nuevo_estado == "RECIBIDO":
            self.recibido_en = fecha_iso
        self.notificar(nuevo_estado, fecha_iso, detalle)
